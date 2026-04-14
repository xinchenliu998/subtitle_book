# 小逻辑字幕书生成器

将句读小逻辑系列的 SRT 字幕文件合并为一本带目录的电子书（EPUB / PDF）。

## 快速开始

### 安装依赖

```bash
# 仅 EPUB 支持
uv pip install -e .

# EPUB + PDF (推荐)
uv pip install -e ".[all]"
```

### 生成电子书

```bash
# 生成 EPUB（默认输出到 build/小逻辑（句读版）.epub）
python build/subtitle_book.py

# 同时生成 PDF（需要 weasyprint 或 pandoc）
python build/subtitle_book.py --pdf

# 指定输出路径
python build/subtitle_book.py -o my_book.epub
```

## 工作原理

1. **扫描** — 自动发现目录下所有 `.srt` 文件
2. **解析** — 从文件名提取集号（如 `［小逻辑10］`）和标题
3. **清洗** — 去除时间轴、序号，合并相邻重复文本
4. **生成** —
   - **EPUB**: 使用 `ebooklib` 生成标准 EPUB3，含 NCX + NAV 双重目录
   - **PDF**: 通过 WeasyPrint 或 Pandoc 转换

## 文件名格式

脚本自动识别以下文件名格式:

```
［小逻辑10］本体论、灵魂论...    → 第 10 集
[句读小逻辑]思想对待客观性...     → 序言/特殊章节（排在最前）
```

## 目录结构

```
小逻辑/
├── pyproject.toml          # 项目配置
├── build/
│   └── subtitle_book.py    # 主脚本
├── README.md
└── *.srt                   # 字幕源文件（放在根目录）
```

## PDF 生成说明

| 方式             | 优点                 | 缺点                        |
| ---------------- | -------------------- | --------------------------- |
| WeasyPrint       | 功能完整，中文支持好 | 需要系统 GTK3/WebKit 依赖   |
| Pandoc + xelatex | 轻量，输出质量高     | 需要用户自行安装 LaTeX 环境 |

推荐使用 WeasyPrint（`uv pip install weasyprint`）。

## 自定义样式

编辑 `subtitle_book.py` 中的 `css_content` 变量，可修改正文字体、字号、行间距等。
