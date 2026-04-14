import pytest
from pathlib import Path
from src.parsers.config import load_config, extract_chapter_info, DEFAULT_CONFIG


def test_load_default_config():
    config = load_config()
    assert config["book"]["title"] == "字幕书"
    assert "filename_pattern" in config


def test_extract_chapter_info_with_chapter_number():
    """有集号: "第10集标题.srt" → (10, "标题")"""
    pattern = r"^(?:第?(\d+)[集话章篇]\s*)?(.+)$"
    num, title = extract_chapter_info("第10集标题.srt", pattern)
    assert num == 10
    assert title == "标题"


def test_extract_chapter_info_no_number():
    """无集号: "序言.srt" → (0, "序言")"""
    pattern = r"^(?:第?(\d+)[集话章篇]\s*)?(.+)$"
    num, title = extract_chapter_info("序言.srt", pattern)
    assert num == 0
    assert title == "序言"


def test_extract_chapter_info_numeric_prefix():
    """无集号标记的数字文件名 → 解析为序言/特殊章节"""
    pattern = r"^(?:第?(\d+)[集话章篇]\s*)?(.+)$"
    # "01.srt" → basename="01"(去扩展名) → 无"集/话/章/篇"标记 → (0, "01")
    num, title = extract_chapter_info("01.srt", pattern)
    assert num == 0
    assert title == "01"