# 字幕书生成器

将 SRT 字幕文件合并为一本带目录的电子书（EPUB / PDF），支持配置文件自定义文件名解析规则和多种输入方式。

## 功能特性

- 支持 **5 种输入方式**：目录扫描、文件列表、glob 模式、JSON 指定顺序
- 支持 **多种 SRT 时间轴格式**（逗号、点号、无毫秒、省略前导零）
- **段落智能合并**：相邻重复文本合并、间隔 <500ms 的字幕合并
- **配置文件驱动**：通过 YAML 自定义文件名解析规则
- **EPUB + PDF 双输出**：NCX + NAV 双重目录

## 安装

```bash
# 仅 EPUB 支持
uv pip install -e .

# EPUB + PDF（推荐）
uv pip install -e ".[all]"
```

## 快速开始

```bash
# 扫描目录生成 EPUB
uv run subtitle-book --dir ./srt_files

# 同时生成 PDF
uv run subtitle-book --dir ./srt_files --pdf

# 指定标题和作者
uv run subtitle-book --dir ./srt_files --title "小逻辑" --author "句读小逻辑"

# JSON 指定顺序（保持文件列表顺序）
uv run subtitle-book --json chapters.json --title "我的书" --pdf
```

## CLI 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--dir`, `-d` | 扫描字幕文件的目录（可多次指定） | `--dir ./ep1 --dir ./ep2` |
| `--files`, `-f` | 直接指定字幕文件（可多次指定） | `--files 01.srt --files 02.srt` |
| `--pattern`, `-p` | glob 模式（支持递归） | `--pattern "**/*.srt"` |
| `--json`, `-j` | JSON 文件路径（含字幕文件列表） | `--json chapters.json` |
| `--output-dir`, `-o` | 输出目录（默认 `build/`） | `--output-dir ./output` |
| `--config`, `-c` | 配置文件路径 | `--config my.yaml` |
| `--title`, `-t` | 书籍标题 | `--title "我的书"` |
| `--author`, `-a` | 作者 | `--author "作者名"` |
| `--pdf` | 同时生成 PDF | `--pdf` |

## 输入方式详解

### 1. 目录扫描

扫描目录下的所有 `.srt` 文件（**非递归**）：

```bash
uv run subtitle-book --dir ./srt_files
# 多个目录
uv run subtitle-book --dir ./ep1 --dir ./ep2
```

### 2. 直接指定文件

显式传入文件路径（支持任意路径）：

```bash
uv run subtitle-book --files ep1/01.srt --files ep2/02.srt
```

### 3. glob 模式

支持递归通配符：

```bash
# 递归扫描所有子目录
uv run subtitle-book --pattern "**/*.srt"

# 特定子目录
uv run subtitle-book --pattern "episodes/**/*.srt"
```

### 4. JSON 文件（保持顺序）

传入包含字幕路径的 JSON 文件，**按文件列表顺序生成章节**，不会自动按集号排序：

```bash
uv run subtitle-book --json chapters.json
```

JSON 格式：

```json
[
  "ep1/01.srt",
  "ep1/02.srt",
  "ep2/intro.srt",
  "ep2/03.srt"
]
```

路径**相对于 JSON 文件所在目录**。示例：

```json
[
  "assets/srt/01.srt",
  "assets/srt/02.srt",
  "assets/srt/03.srt"
]
```

### 5. 混合使用

多种方式可以混合：

```bash
uv run subtitle-book \
  --dir ./ep1 \
  --files ep2/extra.srt \
  --pattern "bonus/**/*.srt"
```

**优先级**：`--json` > `--files` > `--dir` / `--pattern`

## 配置文件

编辑 `configs/default.yaml` 自定义文件名解析规则和 PDF 生成选项：

```yaml
book:
  title: "字幕书"
  author: "作者"

filename_pattern:
  # capture group 1 = 集号(数字)，capture group 2 = 标题
  # 集号为 0 或空表示序言/特殊章节，排在最前
  pattern: "^(?:第?(\\d+)[集话章篇]\\s*)?(.+)$"

encoding: "utf-8"

pdf:
  # Pandoc PDF 字体（留空使用系统默认）
  # Windows 常用: STSong, SimSun, SimHei, Microsoft YaHei
  font: "STSong"
```

### 正则 pattern 说明

- **group 1**：集号（数字），用于排序，设为 0 表示序言/特殊章节
- **group 2**：标题，从文件名中提取

### 常用匹配示例

| 文件名 | 集号 | 标题 |
|--------|------|------|
| `第10集本体论.srt` | 10 | 本体论 |
| `10-标题.srt` | 10 | 标题 |
| `01.srt` | 0 | 01（无标记视为序言） |
| `序言.srt` | 0 | 序言 |

## SRT 时间轴格式

支持以下 4 种变体：

| 格式 | 示例 |
|------|------|
| 标准 SRT（逗号） | `00:00:00,000 --> 00:00:01,500` |
| 点号分隔 | `00:00:00.000 --> 00:00:01.500` |
| 无毫秒 | `00:00:00 --> 00:00:01` |
| 省略小时前导零 | `0:00:00,000 --> 0:00:01,500` |

## 段落合并规则

字幕解析时按以下规则合并：

1. **相邻重复文本**：相同内容只保留一条
2. **间隔 < 500ms**：时间间隔小于 500ms 的相邻字幕视为连续，合并为同一段落

## PDF 生成

| 方式 | 优点 | 缺点 |
|------|------|------|
| WeasyPrint | 功能完整，中文支持好 | 需要系统 GTK3/WebKit 依赖 |
| Pandoc + xelatex | 轻量，输出质量高 | 需要 TeX Live 环境 |

默认 WeasyPrint 优先，失败则回退 Pandoc。

**Pandoc 中文支持**：通过 `xeCJK` 包自动处理中文断行，字体可在配置文件中指定。

安装 WeasyPrint：

```bash
uv pip install weasyprint
```

安装 Pandoc（需配合 TeX Live）：

```bash
# Windows: https://pandoc.org/installing.html
# 或使用 winget
winget install pandoc
```

## 项目结构

```
subtitle_book/
├── src/
│   ├── main.py              # CLI 入口点
│   ├── subtitle_book.py     # 主流程编排
│   ├── models.py            # Chapter / Book 数据模型
│   ├── parsers/
│   │   ├── srt.py           # SRT 解析（多种时间轴格式 + 500ms 合并）
│   │   └── config.py        # YAML 配置加载 + 正则匹配
│   └── generators/
│       ├── epub.py          # EPUB 生成（NCX + NAV 双重目录）
│       └── pdf.py           # PDF 生成（WeasyPrint 优先，Pandoc 备选）
├── configs/
│   └── default.yaml        # 默认配置
├── tests/                   # 单元测试
├── pyproject.toml           # 项目配置
└── CLAUDE.md               # 开发指导
```

## 测试

```bash
# 运行所有测试
.venv/Scripts/python.exe -m pytest tests/ -v

# 运行特定测试
.venv/Scripts/python.exe -m pytest tests/test_srt.py -v
```

注意：`uv run pytest` 在本项目中有模块导入问题，请使用上述命令。

## 故障排除

### PDF 生成失败

1. 确认已安装 WeasyPrint 或 Pandoc
2. WeasyPrint 需要系统 GTK3/WebKit 依赖
3. Pandoc 生成 PDF 需要 TeX Live 环境，并确保配置文件中指定了可用的中文字体

### JSON 文件路径错误

- JSON 中路径相对于 JSON 文件所在目录
- JSON 文件本身不需要和字幕在同一目录
- 确认路径格式正确（使用正斜杠 `/`）
