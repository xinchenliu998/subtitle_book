from __future__ import annotations
import re
from pathlib import Path
from typing import NamedTuple


class SubtitleEntry(NamedTuple):
    """解析出的单条字幕"""
    start_ms: int   # 起始毫秒
    text: str       # 清洗后文本


def _parse_timecode(tc: str) -> int:
    """将时间字符串解析为毫秒数。"""
    tc = tc.replace(',', '.').strip()
    parts = tc.split(':')
    h = int(parts[0])
    m = int(parts[1])
    s = float(parts[2])
    return h * 3600000 + m * 60000 + int(s * 1000)


# SRT 时间轴正则：支持 4 种变体
# 00:00:00,000 --> 00:00:00,000
# 00:00:00.000 --> 00:00:00.000
# 00:00:00 --> 00:00:00
# 0:00:00,000 --> 0:00:00,000
TIMECODE_RE = re.compile(
    r"(\d{1,2}:\d{2}:\d{2}[,.]?\d{0,3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,.]?\d{0,3})"
)
SEQ_RE = re.compile(r"^\d+$")


def parse_srt(filepath: Path) -> list[str]:
    """
    解析 SRT 文件，返回纯文本段落列表。
    支持多种时间轴格式，去除序号和时间轴。
    相邻间隔 < 500ms 的字幕合并为同一段落。
    相邻相同文本合并为一条。
    """
    content = filepath.read_text(encoding="utf-8")
    content = content.replace('\r\n', '\n').replace('\r', '\n')

    entries: list[SubtitleEntry] = []
    prev_end_ms: int = 0  # 上一个保留 entry 的结束时间

    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1

        if not line:
            continue
        if SEQ_RE.match(line):
            continue

        m = TIMECODE_RE.match(line)
        if m:
            start_ms = _parse_timecode(m.group(1))
            end_ms = _parse_timecode(m.group(2))
            if i < len(lines):
                text_line = lines[i].strip()
                i += 1
                clean = re.sub(r'<[^>]+>', '', text_line).strip()
                if clean:
                    gap = start_ms - prev_end_ms
                    # 相邻字幕合并规则：
                    #   - 文本相同：无论 gap 大小，合并为一条（不拼接）
                    #   - 文本不同：仅当 gap < 500ms 时拼接为同一段落；否则开启新段落
                    if entries and entries[-1].text == clean:
                        # 相同文本，合并为一条（不拼接），不更新 prev_end_ms
                        pass
                    elif entries and gap < 500:
                        # 不同文本但 gap < 500ms，拼接为同一段落
                        entries[-1] = entries[-1]._replace(
                            text=entries[-1].text + clean
                        )
                        prev_end_ms = end_ms
                    else:
                        # gap >= 500ms 或没有前一条目，创建新段落
                        entries.append(SubtitleEntry(start_ms=start_ms, text=clean))
                        prev_end_ms = end_ms
            continue

        clean = re.sub(r'<[^>]+>', '', line).strip()
        if clean and entries:
            gap = 0
            if gap < 500:
                entries[-1] = entries[-1]._replace(
                    text=entries[-1].text + clean
                )
            else:
                entries.append(SubtitleEntry(start_ms=0, text=clean))

    paragraphs: list[str] = []
    prev_text: str = ""
    for e in entries:
        if e.text != prev_text:
            paragraphs.append(e.text)
            prev_text = e.text
    return paragraphs