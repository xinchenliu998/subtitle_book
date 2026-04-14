# 项目开发指导

## 项目概述

- **名称**：字幕书生成器
- **功能**：将 SRT 字幕文件合并为带目录的 EPUB/PDF 电子书
- **语言**：Python 3.10+
- **依赖管理**：uv + hatchling
- **入口脚本**：`uv run python -m src.subtitle_book`

## 运行方式

```bash
# 开发调试（推荐）
uv run python -m src.subtitle_book --dir assets/srt

# JSON 指定顺序
uv run python -m src.subtitle_book --json chapters.json --title "我的书"

# 带 PDF
uv run python -m src.subtitle_book --dir assets/srt --pdf

# 安装后运行
subtitle-book --dir ./srt
```

## 代码组织

- 单文件行数控制在 100-200 行，不超过 500 行
- 按功能划分目录：
  - `parsers/` — 解析层（SRT 解析、配置加载）
  - `generators/` — 生成层（EPUB、PDF）
  - `models.py` — 数据模型
  - `subtitle_book.py` — 主流程编排
- 使用 `uv` 管理依赖，pyproject.toml 为配置中心

## 依赖

| 依赖 | 用途 |
|------|------|
| ebooklib | EPUB 生成 |
| pyyaml | 配置文件加载 |
| weasyprint | PDF 生成（可选） |
| pandoc | PDF 生成备选（可选） |

## 测试

```bash
# 运行所有测试
.venv/Scripts/python.exe -m pytest tests/ -v

# 运行特定模块
.venv/Scripts/python.exe -m pytest tests/test_srt.py -v
.venv/Scripts/python.exe -m pytest tests/test_config.py -v
```

注意：`uv run pytest` 有模块导入问题，必须使用 `.venv/Scripts/python.exe -m pytest`。

## 模块说明

### `src/parsers/srt.py`

SRT 解析器。关键接口：

```python
parse_srt(filepath: Path) -> list[str]
# 返回清洗后的段落列表
# 支持 4 种时间轴格式，自动合并相邻重复和间隔 <500ms 的字幕
```

### `src/parsers/config.py`

配置加载器。关键接口：

```python
load_config(config_path: Path | None = None) -> dict[str, Any]
# 加载 YAML 配置，返回包含 book、filename_pattern 等字段的字典

extract_chapter_info(filename: str, pattern: str) -> tuple[int, str]
# 用正则从文件名提取 (集号, 标题)
# 集号 0 = 序言/特殊章节
```

### `src/generators/epub.py`

EPUB 生成器。关键接口：

```python
generate_epub(book: Book, output_path: Path) -> None
# Book 包含 title, author, chapters
# 生成 NCX + NAV 双重目录
```

### `src/generators/pdf.py`

PDF 生成器。关键接口：

```python
generate_pdf(epub_path: Path, pdf_path: Path) -> PDFResult
# PDFResult: SUCCESS / EPUB_MISSING / BOTH_FAILED
# WeasyPrint 优先，失败则回退 Pandoc
```

## 添加新功能

### 新增输入方式

在 `subtitle_book.py` 的 `collect_inputs()` 函数中添加处理逻辑，同时更新 `main()` 中的 argparse 参数。

### 新增解析器

在 `parsers/` 目录下新建模块（如 `vtt.py`），实现统一的解析接口：

```python
def parse_vtt(filepath: Path) -> list[str]:
    """返回清洗后的段落列表。"""
    ...
```

### 新增生成器

在 `generators/` 目录下新建模块，实现统一的生成接口：

```python
def generate_mobi(book: Book, output_path: Path) -> bool:
    """返回是否成功。"""
    ...
```

## 构建与发布

```bash
# editable 安装（开发用）
uv pip install -e .

# editable 安装 + PDF 依赖
uv pip install -e ".[all]"

# 构建 wheel
uv build

# hatchling 打包配置
# 位于 pyproject.toml 的 [tool.hatch.build.targets.wheel]
```

## 目录结构

```
src/
├── main.py              # CLI 入口点（调用 subtitle_book.main）
├── subtitle_book.py     # 主流程编排（collect_inputs、collect_chapters、main）
├── models.py           # Chapter(NamedTuple) / Book(dataclass)
├── parsers/
│   ├── __init__.py
│   ├── srt.py          # SRT 解析（时间轴兼容 + 500ms 合并）
│   └── config.py       # YAML 配置 + 文件名正则提取
├── generators/
│   ├── __init__.py
│   ├── epub.py         # EPUB 生成（ebooklib）
│   └── pdf.py          # PDF 生成（WeasyPrint / Pandoc）
configs/
└── default.yaml        # 默认配置
tests/                   # 单元测试（pytest）
├── test_models.py
├── test_srt.py
├── test_config.py
└── test_generators.py
```

## 注意事项

- 所有路径处理使用 `pathlib.Path`，跨平台兼容
- 编码统一 UTF-8，不做自动检测
- SRT 时间轴解析正则：`^\d{1,2}:\d{2}:\d{2}[,.]?\d{0,3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[,.]?\d{0,3}$`
- 段落合并：相邻相同文本去重，时间间隔 <500ms 的相邻字幕合并
