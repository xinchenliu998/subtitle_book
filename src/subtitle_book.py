"""
字幕书生成器 — 将 SRT 字幕文件合并为带目录的电子书（EPUB/PDF）
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.models import Book, Chapter
from src.parsers.srt import parse_srt
from src.parsers.config import load_config, extract_chapter_info
from src.generators.epub import generate_epub
from src.generators.pdf import generate_pdf, PDFResult


# ─────────────────────────── 输入收集 ────────────────────────────

def collect_inputs(
    dirs: list[Path] | None = None,
    files: list[Path] | None = None,
    pattern: str | None = None,
    srt_dir: Path | None = None,
) -> list[Path]:
    """
    统一处理四种输入方式，返回去重 SRT 文件路径列表。
    - --dir: 非递归扫描目录
    - --files: 直接指定文件列表
    - --pattern: glob 模式，支持递归（如 "**/*.srt"）
    - --srt_dir: 默认扫描目录（兼容旧参数）
    """
    results: set[Path] = set()
    search_bases: list[Path] = []

    if dirs:
        search_bases.extend(dirs)
    elif srt_dir:
        search_bases.append(srt_dir)

    # 目录扫描（默认 *.srt，不递归）
    for d in search_bases:
        results.update(d.glob("*.srt"))

    # 显式文件列表
    if files:
        results.update(f for f in files if f.suffix.lower() == ".srt")

    # glob 模式（支持递归，如 "**/*.srt"）
    if pattern:
        base = search_bases[0] if search_bases else Path(".")
        results.update(base.glob(pattern))

    return sorted(results)


def collect_inputs_from_json(json_path: Path) -> list[Path]:
    """
    从 JSON 文件读取字幕文件路径列表。
    JSON 格式: ["path/to/01.srt", "path/to/02.srt", ...]
    路径相对于 JSON 文件所在目录。
    返回保持 JSON 中的顺序。
    """
    with open(json_path, encoding="utf-8") as f:
        paths: list[str] = json.load(f)

    base_dir = json_path.parent
    srt_files = []
    for p in paths:
        path = base_dir / p
        if path.suffix.lower() == ".srt" and path.exists():
            srt_files.append(path)
        else:
            print(f"[WARN] 跳过不存在或非 SRT 文件: {path}")
    return srt_files


def collect_chapters(srt_files: list[Path], pattern: str, sort: bool = True) -> list[Chapter]:
    """
    解析 SRT 文件列表为 Chapter 列表。
    sort=True 时按集号排序（number=0 序言最前）；sort=False 时保持文件顺序。
    """
    chapters = []
    for fp in srt_files:
        num, title = extract_chapter_info(fp.name, pattern)
        paragraphs = parse_srt(fp)
        if paragraphs:
            chapters.append(Chapter(
                number=num,
                title=title,
                filename=fp.name,
                paragraphs=paragraphs,
            ))
    if sort:
        chapters.sort(key=lambda c: (c.number if c.number != 0 else -1, c.filename))
    return chapters


# ─────────────────────────── 主流程 ────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="字幕书生成器")
    parser.add_argument("--dir", "-d", action="append", type=Path,
                        help="扫描字幕文件的目录（可多次指定）")
    parser.add_argument("--files", "-f", action="append", type=Path,
                        help="直接指定字幕文件（可多次指定）")
    parser.add_argument("--pattern", "-p", type=str,
                        help="glob 模式，如 '**/*.srt'（支持递归）")
    parser.add_argument("--json", "-j", type=Path,
                        help="JSON 文件路径，其中包含字幕文件路径列表（保持顺序）")
    parser.add_argument("--output-dir", "-o", type=Path, default=Path("build"),
                        help="输出目录（默认: build/）")
    parser.add_argument("--config", "-c", type=Path,
                        help="配置文件路径（默认: configs/default.yaml）")
    parser.add_argument("--title", "-t", type=str,
                        help="书籍标题（默认: 从配置文件读取）")
    parser.add_argument("--author", "-a", type=str,
                        help="作者（默认: 从配置文件读取）")
    parser.add_argument("--pdf", action="store_true",
                        help="同时生成 PDF")
    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)
    title = args.title or config["book"]["title"]
    author = args.author or config["book"]["author"]
    filename_pattern = config["filename_pattern"]["pattern"]

    # 收集 SRT 文件
    if args.json:
        srt_files = collect_inputs_from_json(args.json)
        sort_chapters = False
    else:
        dirs = args.dir if args.dir else None
        files = args.files if args.files else None
        pattern = args.pattern
        srt_files = collect_inputs(dirs=dirs, files=files, pattern=pattern, srt_dir=Path("."))
        sort_chapters = True

    if not srt_files:
        print("[ERROR] 未找到任何字幕文件")
        sys.exit(1)

    print(f"[INFO] 找到 {len(srt_files)} 个字幕文件")

    # 解析章节
    chapters = collect_chapters(srt_files, filename_pattern, sort=sort_chapters)
    print(f"[INFO] 共 {len(chapters)} 章")

    # 预览前几章
    print("\n=== 章节预览 ===")
    for ch in chapters[:5]:
        preview = "".join(ch.paragraphs[:2])[:40]
        print(f"  [{ch.number:3}] {ch.title[:50]}  | {preview}...")
    if len(chapters) > 5:
        print(f"  ... 共 {len(chapters)} 章")
    print()

    # 构建书籍
    book = Book(title=title, author=author, chapters=chapters)

    # 输出路径
    output_dir = args.output_dir
    epub_path = output_dir / f"{title}.epub"
    pdf_path = output_dir / f"{title}.pdf"

    # 生成 EPUB
    print(f"[INFO] 生成 EPUB: {epub_path}")
    generate_epub(book, epub_path)

    # 生成 PDF
    if args.pdf:
        print(f"[INFO] 生成 PDF: {pdf_path}")
        result = generate_pdf(epub_path, pdf_path)
        if result == PDFResult.BOTH_FAILED:
            print("[WARN] PDF 生成失败（EPUB 已成功生成）")


if __name__ == "__main__":
    main()
