# SRT 系列字幕书生成器 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将单一 `subtitle_book.py` 重构为模块化架构，支持多种 SRT 时间轴格式、配置文件驱动的文件名解析、四种输入方式，输出 EPUB/PDF 带目录。

**Architecture:**
- 解析层：`parsers/config.py`（YAML配置加载 + 正则匹配）、`parsers/srt.py`（SRT解析，兼容多种时间轴格式）
- 生成层：`generators/epub.py`（EPUB生成）、`generators/pdf.py`（WeasyPrint优先，Pandoc备选）
- 模型层：`models.py`（Chapter/Book数据模型）
- 主流程：`subtitle_book.py`（编排）、`main.py`（CLI入口）
- 配置文件：`configs/default.yaml`

**Tech Stack:** Python 3.10+, ebooklib, weasyprint, pyyaml, re

---

## 文件结构

```
src/
├── main.py                  # CLI 入口（现有，保留）
├── subtitle_book.py         # 重构主流程编排（重建）
├── models.py                # 新建：Chapter/Book 模型
├── parsers/
│   ├── __init__.py          # 新建
│   ├── srt.py               # 新建：SRT 解析器
│   └── config.py            # 新建：配置加载 + 文件名正则
├── generators/
│   ├── __init__.py          # 新建
│   ├── epub.py              # 新建：EPUB 生成器
│   └── pdf.py               # 新建：PDF 生成器
configs/
└── default.yaml             # 新建：默认配置
tests/
├── test_models.py           # 新建：数据模型测试
├── test_srt.py              # 新建：SRT 解析测试
├── test_config.py           # 新建：配置加载测试
└── test_generators.py       # 新建：生成器测试（EPUB）
```

---

## Task 1: 项目目录与依赖准备

**Files:**
- Create: `src/parsers/__init__.py`
- Create: `src/parsers/srt.py`
- Create: `src/parsers/config.py`
- Create: `src/generators/__init__.py`
- Create: `src/generators/epub.py`
- Create: `src/generators/pdf.py`
- Create: `src/models.py`
- Create: `configs/default.yaml`
- Create: `tests/test_models.py`
- Create: `tests/test_srt.py`
- Create: `tests/test_config.py`
- Create: `tests/test_generators.py`
- Modify: `pyproject.toml`（添加 pyyaml 依赖）
- Modify: `src/main.py`（适配新模块结构）
- Modify: `src/subtitle_book.py`（重构）

- [ ] **Step 1: 安装 pyyaml 依赖**

Run: `cd e:/workSpace/source-code/my-project/subtitle_book && uv add pyyaml`

- [ ] **Step 2: 创建目录结构**

Run: `mkdir -p src/parsers src/generators configs tests`

- [ ] **Step 3: 创建空 `__init__.py` 文件**

```bash
touch src/parsers/__init__.py src/generators/__init__.py
```

---

## Task 2: `models.py` — 数据模型

**Files:**
- Create: `src/models.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_models.py
import pytest
from src.models import Chapter, Book

def test_chapter_creation():
    ch = Chapter(number=1, title="标题", filename="01.srt", paragraphs=["段落1", "段落2"])
    assert ch.number == 1
    assert ch.title == "标题"
    assert len(ch.paragraphs) == 2

def test_book_creation():
    chapters = [
        Chapter(number=1, title="第一章", filename="01.srt", paragraphs=["p1"]),
        Chapter(number=0, title="序言", filename="00.srt", paragraphs=["p0"]),
    ]
    book = Book(title="书名", author="作者", chapters=chapters)
    assert book.title == "书名"
    assert len(book.chapters) == 2
```

Run: `pytest tests/test_models.py -v`

- [ ] **Step 2: 实现 `src/models.py`**

```python
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
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
```

Run: `pytest tests/test_models.py -v` → PASS

- [ ] **Step 3: Commit**

```bash
git add src/models.py tests/test_models.py
git commit -m "feat: 添加 Chapter/Book 数据模型"
```

---

## Task 3: `parsers/srt.py` — SRT 解析器

**Files:**
- Create: `src/parsers/srt.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_srt.py
import pytest
from src.parsers.srt import parse_srt, collect_chapters

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
    # 前两句间隔 200ms (< 500ms)，合并；第三句独立
    assert paragraphs == ["第一句第二句", "第三句（间隔>500ms，独立段落）"]
```

Run: `pytest tests/test_srt.py -v` → 应全部 FAIL（未实现）

- [ ] **Step 2: 实现 `src/parsers/srt.py`**

```python
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
    # 统一逗号为点号
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
    current_text: str = ""
    current_start_ms: int = 0
    prev_end_ms: int = 0

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
            # 下一行为字幕文本
            if i < len(lines):
                text_line = lines[i].strip()
                i += 1
                clean = re.sub(r'<[^>]+>', '', text_line).strip()
                if clean:
                    # 判断是否与前一条合并（间隔 < 500ms）
                    gap = start_ms - prev_end_ms
                    if entries and gap < 500:
                        # 合并到前一条
                        entries[-1] = entries[-1]._replace(
                            text=entries[-1].text + clean
                        )
                    else:
                        entries.append(SubtitleEntry(start_ms=start_ms, text=clean))
                    prev_end_ms = end_ms
            continue

        # 普通文本行（部分 SRT 无时间轴行）
        clean = re.sub(r'<[^>]+>', '', line).strip()
        if clean and entries:
            gap = 0  # 无时间轴时视为连续
            if gap < 500:
                entries[-1] = entries[-1]._replace(
                    text=entries[-1].text + clean
                )
            else:
                entries.append(SubtitleEntry(start_ms=0, text=clean))

    # 去重相邻相同文本
    paragraphs: list[str] = []
    prev_text: str = ""
    for e in entries:
        if e.text != prev_text:
            paragraphs.append(e.text)
            prev_text = e.text
    return paragraphs
```

Run: `pytest tests/test_srt.py -v` → 应全部 PASS

- [ ] **Step 3: Commit**

```bash
git add src/parsers/srt.py tests/test_srt.py
git commit -m "feat: 添加 SRT 解析器，支持多种时间轴格式"
```

---

## Task 4: `parsers/config.py` — 配置加载 + 文件名正则

**Files:**
- Create: `src/parsers/config.py`
- Create: `configs/default.yaml`

- [ ] **Step 1: 编写测试**

```python
# tests/test_config.py
import pytest
from pathlib import Path
from src.parsers.config import load_config, extract_chapter_info, DEFAULT_CONFIG

def test_load_default_config(tmp_path):
    config = load_config()
    assert config["book"]["title"] == "字幕书"
    assert "filename_pattern" in config

def test_extract_chapter_number_and_title():
    """默认 pattern: ^(?:第?(\\d+)[集话章篇]\\s*)?(.+)$"""
    pattern = r"^(?:第?(\d+)[集话章篇]\s*)?(.+)$"

    # 无集号: "序言.srt" → (0, "序言")
    num, title = extract_chapter_info("序言.srt", pattern)
    assert num == 0
    assert title == "序言"

    # 有集号: "第10集标题.srt" → (10, "标题")
    num, title = extract_chapter_info("第10集标题.srt", pattern)
    assert num == 10

    # 纯数字: "01.srt" → (1, "01")
    num, title = extract_chapter_info("01.srt", pattern)
    assert num == 1
```

Run: `pytest tests/test_config.py -v` → FAIL

- [ ] **Step 2: 创建 `configs/default.yaml`**

```yaml
book:
  title: "字幕书"
  author: "作者"

filename_pattern:
  # capture group 1 = 集号(数字)，capture group 2 = 标题
  # 集号为 0 或空表示序言/特殊章节，排在最前
  pattern: "^(?:第?(\\d+)[集话章篇]\\s*)?(.+)$"

encoding: "utf-8"
```

- [ ] **Step 3: 实现 `src/parsers/config.py`**

```python
from __future__ import annotations
import re
import yaml
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "configs" / "default.yaml"

DEFAULT_CONFIG: dict[str, Any] = {
    "book": {
        "title": "字幕书",
        "author": "作者",
    },
    "filename_pattern": {
        "pattern": r"^(?:第?(\d+)[集话章篇]\s*)?(.+)$",
    },
    "encoding": "utf-8",
}


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """加载 YAML 配置文件，缺失字段使用默认值。"""
    path = config_path or DEFAULT_CONFIG_PATH
    if not path.exists():
        return DEFAULT_CONFIG.copy()

    with open(path, encoding="utf-8") as f:
        user_config = yaml.safe_load(f) or {}

    # 深度合并默认值
    config = DEFAULT_CONFIG.copy()
    for key, value in user_config.items():
        if key in config and isinstance(config[key], dict):
            config[key].update(value)
        else:
            config[key] = value
    return config


def extract_chapter_info(filename: str, pattern: str) -> tuple[int, str]:
    """
    用正则从文件名提取集号和标题。
    Returns: (number, title)
    - number=0 表示序言/特殊章节
    - 无法解析时 number=0，title=文件名（去扩展名）
    """
    basename = Path(filename).stem
    compiled = re.compile(pattern)
    m = compiled.search(basename)
    if not m:
        return 0, basename

    num_str = m.group(1)
    title = m.group(2).strip() if m.lastindex >= 2 else basename

    if num_str:
        try:
            return int(num_str), title
        except ValueError:
            pass
    return 0, title
```

Run: `pytest tests/test_config.py -v` → PASS

- [ ] **Step 4: Commit**

```bash
git add src/parsers/config.py configs/default.yaml tests/test_config.py
git commit -m "feat: 添加配置加载器和文件名解析器"
```

---

## Task 5: `generators/epub.py` — EPUB 生成器

**Files:**
- Create: `src/generators/epub.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_generators.py
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
    generate_epub(Book(title="书名", author="作者", chapters=chapters), output)
    assert output.exists()
```

Run: `pytest tests/test_generators.py -v` → FAIL

- [ ] **Step 2: 实现 `src/generators/epub.py`**

参考原有 `subtitle_book.py` 中的 `generate_epub` 函数，保持接口一致（接收 `list[Chapter]` + 输出路径），使用 ebooklib 生成 NCX + NAV 双重目录。

- [ ] **Step 3: Run test**

Run: `pytest tests/test_generators.py -v` → PASS

- [ ] **Step 4: Commit**

```bash
git add src/generators/epub.py tests/test_generators.py
git commit -m "feat: 添加 EPUB 生成器"
```

---

## Task 6: `generators/pdf.py` — PDF 生成器

**Files:**
- Create: `src/generators/pdf.py`

- [ ] **Step 1: 编写测试**

```python
# 略（PDF 生成依赖外部库，用集成测试验证）
```

- [ ] **Step 2: 实现 `src/generators/pdf.py`**

```python
from __future__ import annotations
from pathlib import Path
from src.models import Book
from enum import Enum


class PDFResult(Enum):
    SUCCESS = "success"           # PDF 生成成功
    EPUB_MISSING = "epub_missing" # EPUB 文件不存在
    BOTH_FAILED = "both_failed"    # EPUB 存在但 PDF 生成失败


def generate_pdf(epub_path: Path, pdf_path: Path) -> PDFResult:
    """
    PDF 生成：WeasyPrint 优先，Pandoc 备选。
    返回结果状态，区分"EPUB 存在但 PDF 失败"和"EPUB 不存在"。
    """
    if not epub_path.exists():
        return PDFResult.EPUB_MISSING

    # 先尝试 WeasyPrint
    if _try_weasyprint(epub_path, pdf_path):
        return PDFResult.SUCCESS
    # 回退 Pandoc
    if _try_pandoc(epub_path, pdf_path):
        return PDFResult.SUCCESS
    return PDFResult.BOTH_FAILED


def _try_weasyprint(epub_path: Path, pdf_path: Path) -> bool:
    try:
        import weasyprint
    except ImportError:
        return False
    try:
        wp = weasyprint.HTML(filename=str(epub_path))
        wp.write_pdf(str(pdf_path))
        return True
    except Exception:
        return False


def _try_pandoc(epub_path: Path, pdf_path: Path) -> bool:
    import subprocess, shutil, tempfile
    pandoc = shutil.which("pandoc")
    if not pandoc:
        return False
    # 生成中间 Markdown，通过 pandoc 转 PDF
    # ...（参考原有实现）
    return True
```

- [ ] **Step 3: Commit**

```bash
git add src/generators/pdf.py
git commit -m "feat: 添加 PDF 生成器（WeasyPrint/Pandoc）"
```

---

## Task 7: `subtitle_book.py` — 主流程重构

**Files:**
- Modify: `src/subtitle_book.py`（重建）
- Modify: `src/main.py`（适配新模块）

- [ ] **Step 1: 实现 `collect_inputs` 函数**

```python
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
    pattern 的 glob 基准目录为 dirs[0]（如有）或 srt_dir 或当前目录。
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
```

- [ ] **Step 2: 实现 `collect_chapters` 函数**

```python
from src.models import Chapter
from src.parsers.srt import parse_srt
from src.parsers.config import extract_chapter_info

def collect_chapters(srt_files: list[Path], pattern: str) -> list[Chapter]:
    """解析 SRT 文件列表为 Chapter 列表，按集号排序。"""
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
    chapters.sort(key=lambda c: (c.number if c.number != 0 else -1, c.filename))
    return chapters
```

- [ ] **Step 3: 重写 `main()` 函数**

整合所有模块，提供 `--dir`、`--files`、`--pattern`、`--output-dir`、`--config`、`--pdf` 等 CLI 参数。

- [ ] **Step 4: 修改 `main.py`**

```python
from src.subtitle_book import main
main()
```

- [ ] **Step 5: 运行集成测试**

```bash
# 在项目根目录放置测试 SRT 文件，运行完整流程
uv run subtitle-book --dir . --pdf
```

- [ ] **Step 6: Commit**

```bash
git add src/subtitle_book.py src/main.py
git commit -m "refactor: 重构主流程，整合各模块"
```

---

## Task 8: 清理旧文件

**Files:**
- Delete: `src/subtitle_book.py`（旧版本 monolithic 实现，已被重构替代）

- [ ] **Step 1: 删除旧实现文件**

旧实现已由 Task 7 的重构替代，确认删除。

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "chore: 清理旧文件"
```
