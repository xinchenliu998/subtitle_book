import pytest
from src.parsers.srt import parse_srt, SubtitleEntry

def test_parse_srt_standard_timeformat(tmp_path):
    """标准时间轴: 00:00:00,000 --> 00:00:00,000"""
    srt_content = """1
00:00:01,000 --> 00:00:03,500
第一句字幕

2
00:00:04,000 --> 00:00:06,000
第二句字幕
"""
    fp = tmp_path / "test.srt"
    fp.write_text(srt_content, encoding="utf-8")
    paragraphs = parse_srt(fp)
    assert paragraphs == ["第一句字幕", "第二句字幕"]

def test_parse_srt_dot_timeformat(tmp_path):
    """点号分隔符: 00:00:00.000 --> 00:00:00.000"""
    srt_content = """1
00:00:01.000 --> 00:00:03.500
第一句字幕
"""
    fp = tmp_path / "test.srt"
    fp.write_text(srt_content, encoding="utf-8")
    paragraphs = parse_srt(fp)
    assert paragraphs == ["第一句字幕"]

def test_parse_srt_no_milliseconds(tmp_path):
    """无毫秒: 00:00:00 --> 00:00:00"""
    srt_content = """1
00:00:01 --> 00:00:03
第一句字幕
"""
    fp = tmp_path / "test.srt"
    fp.write_text(srt_content, encoding="utf-8")
    paragraphs = parse_srt(fp)
    assert paragraphs == ["第一句字幕"]

def test_parse_srt_no_leading_zero(tmp_path):
    """省略小时前导零: 0:00:00,000 --> 0:00:00,000"""
    srt_content = """1
0:00:01,000 --> 0:00:03,500
第一句字幕
"""
    fp = tmp_path / "test.srt"
    fp.write_text(srt_content, encoding="utf-8")
    paragraphs = parse_srt(fp)
    assert paragraphs == ["第一句字幕"]

def test_parse_srt_deduplicate_adjacent(tmp_path):
    """相邻重复字幕合并"""
    srt_content = """1
00:00:01,000 --> 00:00:02,000
重复内容

2
00:00:02,100 --> 00:00:03,000
重复内容

3
00:00:03,100 --> 00:00:04,000
不同内容
"""
    fp = tmp_path / "test.srt"
    fp.write_text(srt_content, encoding="utf-8")
    paragraphs = parse_srt(fp)
    assert paragraphs == ["重复内容", "不同内容"]

def test_parse_srt_500ms_merge(tmp_path):
    """间隔小于 500ms 的相邻字幕合并为同一段落"""
    srt_content = """1
00:00:01,000 --> 00:00:01,400
第一句

2
00:00:01,600 --> 00:00:02,000
第二句

3
00:00:02,600 --> 00:00:03,000
第三句（间隔>500ms，独立段落）
"""
    fp = tmp_path / "test.srt"
    fp.write_text(srt_content, encoding="utf-8")
    paragraphs = parse_srt(fp)
    # 前两句间隔 200ms (< 500ms)，合并；第三句间隔 600ms (> 500ms)，独立
    assert paragraphs == ["第一句第二句", "第三句（间隔>500ms，独立段落）"]