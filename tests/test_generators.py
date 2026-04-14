import pytest
from pathlib import Path
from src.models import Chapter, Book
from src.generators.epub import generate_epub


def test_generate_epub_basic(tmp_path):
    chapters = [
        Chapter(number=1, title="第一章", filename="01.srt", paragraphs=["第一段", "第二段"]),
        Chapter(number=0, title="序言", filename="00.srt", paragraphs=["序言段"]),
    ]
    output = tmp_path / "test.epub"
    book = Book(title="测试书", author="测试作者", chapters=chapters)
    generate_epub(book, output)
    assert output.exists()