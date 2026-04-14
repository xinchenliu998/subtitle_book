# SRT 系列字幕书生成器 — 设计文档

## 概述

将多个 SRT 字幕文件合并为一本带目录的电子书（EPUB/PDF），支持通过配置文件自定义文件名解析规则。

## 输入方式

支持四种输入方式，混合使用：

1. **目录扫描**：`--dir /path/to/srt/` 自动发现目录下所有 `.srt` 文件
2. **显式列表**：`srt1.srt srt2.srt` 逐个指定文件
3. **glob 模式**：`--pattern "episode/*.srt"` 支持通配符
4. **混合模式**：以上三种可同时使用

统一由 `collect_inputs()` 处理。

## 配置文件格式

`configs/default.yaml`:

```yaml
book:
  title: "我的字幕书"
  author: "作者名"

filename_pattern:
  # capture group 1 = 集号(数字)，capture group 2 = 标题
  # 集号为 0 或空表示序言/特殊章节，排在最前
  pattern: "^(?:第?(\\d+)[集话章篇]\\s*)?(.+)$"

encoding: "utf-8"
```

用户编辑配置文件即可适配自己的命名规则，无需修改代码。

## SRT 时间轴格式兼容

支持以下变体：
- `00:00:00,000 --> 00:00:00,000`（标准 SRT，逗号）
- `00:00:00.000 --> 00:00:00.000`（点号）
- `00:00:00 --> 00:00:00`（无毫秒）
- `0:00:00,000 --> 0:00:00,000`（省略小时前导零）

## 数据模型

```python
class Chapter(NamedTuple):
    number: int          # 集号，0=序言/特殊章节
    title: str           # 清洗后的标题
    filename: str        # 原始文件名
    paragraphs: list[str] # 清洗后的段落列表

@dataclass
class Book:
    title: str
    author: str
    chapters: list[Chapter]
```

## 模块划分

| 文件 | 职责 |
|------|------|
| `src/main.py` | CLI 入口 |
| `src/models.py` | 数据模型 |
| `src/parsers/config.py` | YAML 配置加载 + 正则匹配 |
| `src/parsers/srt.py` | SRT 解析（多种时间轴格式兼容） |
| `src/generators/epub.py` | EPUB 生成 |
| `src/generators/pdf.py` | PDF 生成（WeasyPrint 优先，Pandoc 备选） |
| `src/subtitle_book.py` | 主流程编排 |
| `configs/default.yaml` | 默认配置 |

## PDF 生成流程

```
EPUB 生成成功 → 尝试 WeasyPrint → 成功 → 输出 PDF
                              → 失败 → 尝试 Pandoc → 成功 → 输出 PDF
                                                           → 失败 → 报错，EPUB 已生成
EPUB 生成失败 → 报错
```

## 输出

- EPUB：完整 NCX + NAV 双重目录
- PDF：通过 WeasyPrint 或 Pandoc 生成
- 输出目录：`build/`（可通过 `--output-dir` 指定）

## 编码

统一使用 UTF-8，不做自动编码检测。
