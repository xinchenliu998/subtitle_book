import pytest
from src.models import Chapter, Book


def test_chapter_creation():
    ch = Chapter(number=1, title="标题", filename="01.srt", paragraphs=["段落1", "段落2"])
    assert ch.number == 1
    assert len(ch.paragraphs) == 2


def test_book_creation():
    chapters = [
        Chapter(number=1, title="第一章", filename="01.srt", paragraphs=["p1"]),
        Chapter(number=0, title="序言", filename="00.srt", paragraphs=["p0"]),
    ]
    book = Book(title="书名", author="作者", chapters=chapters)
    assert book.title == "书名"
    assert len(book.chapters) == 2
