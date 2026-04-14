from __future__ import annotations
from dataclasses import dataclass, field
from typing import NamedTuple


class Chapter(NamedTuple):
    """单章内容"""
    number: int           # 集号，0=序言/特殊章节
    title: str            # 清洗后的标题
    filename: str         # 原始文件名（含扩展名）
    paragraphs: list[str]  # 清洗后的段落列表


@dataclass
class Book:
    """整本书"""
    title: str
    author: str
    chapters: list[Chapter] = field(default_factory=list)
