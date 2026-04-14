"""EPUB 生成器"""

from __future__ import annotations

import html
from pathlib import Path

from src.models import Book, Chapter


def generate_epub(book: Book, output_path: Path) -> None:
    """
    使用 ebooklib 生成 EPUB 文件。

    Args:
        book: 包含 title, author, chapters 的书籍对象
        output_path: 输出 EPUB 文件路径
    """
    # 延迟导入，避免未安装时报错
    from ebooklib import epub
    from ebooklib.epub import EpubBook, EpubHtml

    # 创建书籍
    epub_book = EpubBook()
    epub_book.set_identifier(f"subtitle-book-{hash(book.title)}")
    epub_book.set_title(book.title)
    epub_book.set_language("zh-CN")
    epub_book.add_author(book.author)

    # ── 样式 (内联 CSS) ──
    css_content = """
    body {
        font-family: "Noto Serif CJK SC", "Source Han Serif CN", serif;
        font-size: 1.1em;
        line-height: 1.8;
        text-align: justify;
        margin: 1em 1.2em;
        color: #333;
    }
    h1 {
        font-size: 1.6em;
        text-align: center;
        margin: 1.5em 0 0.8em;
        border-bottom: 1px solid #ccc;
        padding-bottom: 0.3em;
        color: #1a1a1a;
    }
    h2 {
        font-size: 1.3em;
        margin: 1.2em 0 0.5em;
        color: #2c2c2c;
    }
    p {
        text-indent: 2em;
        margin: 0.3em 0;
    }
    .chapter-title {
        font-size: 1.4em;
        font-weight: bold;
        text-align: center;
        margin: 1.5em 0 0.5em;
        color: #111;
    }
    .episode-number {
        text-align: center;
        color: #888;
        font-size: 0.85em;
        margin-bottom: 0.3em;
    }
    """

    # 添加样式文件
    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=css_content.encode("utf-8"),
    )
    epub_book.add_item(nav_css)

    # ── 排序章节: number 0 (序言) 最前，其余按 number 升序 ──
    sorted_chapters = sorted(book.chapters, key=lambda c: (c.number if c.number != 0 else -1, c.filename))

    # ── 生成章节 ──
    epub_chapters: list[EpubHtml] = []

    for ch in sorted_chapters:
        epub_ch = epub.EpubHtml(
            title=ch.title,
            file_name=f"chapter_{ch.number:03d}.xhtml",
            lang="zh-CN",
        )
        # 构建章节 HTML
        body_parts: list[str] = []

        # 集号 (仅 number > 0 时显示)
        if ch.number > 0:
            body_parts.append(f'<p class="episode-number">第 {ch.number} 集</p>')
        body_parts.append(f'<h1 class="chapter-title">{html.escape(ch.title)}</h1>')

        # 正文段落
        for para in ch.paragraphs:
            body_parts.append(f"<p>{html.escape(para)}</p>")

        epub_ch.content = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <meta charset="UTF-8"/>
  <title>{html.escape(ch.title)}</title>
</head>
<body>
{chr(10).join(body_parts)}
</body>
</html>"""
        epub_book.add_item(epub_ch)
        epub_chapters.append(epub_ch)

    # ── 目录 (NCX + NAV) ──
    epub_book.toc = tuple(epub_chapters)

    # NCX (兼容旧阅读器)
    epub_book.add_item(epub.EpubNcx())

    # NAV (EPUB3 目录)
    nav_file = epub.EpubNav(
        uid="nav",
        file_name="nav.xhtml",
    )
    epub_book.add_item(nav_file)

    # ── 脊柱 (reading order) ──
    epub_book.spine = ["nav"] + epub_chapters

    # ── 写文件 ──
    output_path.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(output_path), epub_book, {})