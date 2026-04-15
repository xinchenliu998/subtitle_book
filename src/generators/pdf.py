"""
PDF 生成器 — WeasyPrint 优先，Pandoc 备选。
"""

from __future__ import annotations

import subprocess
import shutil
import tempfile
from enum import Enum
from pathlib import Path

from src.models import Book


class PDFResult(Enum):
    SUCCESS = "success"           # PDF 生成成功
    EPUB_MISSING = "epub_missing"  # EPUB 文件不存在
    BOTH_FAILED = "both_failed"  # EPUB 存在但 PDF 生成失败


def generate_pdf(epub_path: Path, pdf_path: Path, pdf_font: str | None = None) -> PDFResult:
    """
    PDF 生成：WeasyPrint 优先，Pandoc 备选。
    pdf_font: Pandoc PDF 使用的字体（为空则不指定，使用系统默认）。
    返回结果状态，区分"EPUB 存在但 PDF 失败"和"EPUB 不存在"。
    """
    if not epub_path.exists():
        return PDFResult.EPUB_MISSING

    if _try_weasyprint(epub_path, pdf_path):
        return PDFResult.SUCCESS
    if _try_pandoc(epub_path, pdf_path, pdf_font):
        return PDFResult.SUCCESS
    return PDFResult.BOTH_FAILED


def _try_weasyprint(epub_path: Path, pdf_path: Path) -> bool:
    """尝试使用 WeasyPrint 生成 PDF。"""
    try:
        import weasyprint
    except (ImportError, OSError):
        return False

    print("[INFO] 使用 WeasyPrint 生成 PDF (较慢，请耐心) ...")
    try:
        wp = weasyprint.HTML(filename=str(epub_path))
        wp.write_pdf(str(pdf_path))
        print(f"[OK] PDF 已生成: {pdf_path}")
        return True
    except Exception as e:
        print(f"[ERROR] WeasyPrint PDF 生成失败: {e}")
        return False


def _try_pandoc(epub_path: Path, pdf_path: Path, pdf_font: str | None = None) -> bool:
    """
    尝试使用 Pandoc 从 EPUB 生成 PDF。
    通过 EPUB -> HTML -> Markdown -> PDF 的方式转换。
    """
    pandoc = shutil.which("pandoc")
    if not pandoc:
        print("[WARN] pandoc 未安装，跳过 PDF 生成")
        return False

    print("[INFO] 使用 Pandoc 生成 PDF ...")
    try:
        cmd = [
            pandoc, str(epub_path), "-o", str(pdf_path),
            "--pdf-engine=xelatex",
            "--standalone",
        ]
        if pdf_font:
            # xeCJK header for Chinese font support
            cjk_header = f"\\usepackage{{xeCJK}}\\setCJKmainfont{{{pdf_font}}}"
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False, encoding='utf-8') as f:
                f.write(cjk_header)
                header_file = f.name
            cmd += ["--include-in-header", header_file]
            cmd += ["-V", f"mainfont={pdf_font}"]
        cmd += ["--quiet"]
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode == 0:
            print(f"[OK] PDF 已生成: {pdf_path}")
            return True
        else:
            print(f"[WARN] pandoc PDF 生成非零退出: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print("[ERROR] pandoc 超时 (5min)")
        return False
    except Exception as e:
        print(f"[ERROR] pandoc 调用失败: {e}")
        return False
