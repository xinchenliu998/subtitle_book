# 字幕书生成器

将 SRT 字幕文件合并为一本带目录的电子书（EPUB / PDF），支持配置文件自定义文件名解析规则。

## 安装

```bash
uv pip install -e .
```

如需 PDF 生成（推荐）：

```bash
uv pip install -e ".[all]"
```

## 快速开始

```bash
# 扫描目录生成 EPUB
uv run subtitle-book --dir ./srt_files

# 同时生成 PDF
uv run subtitle-book --dir ./srt_files --pdf

# 完整示例
uv run subtitle-book --dir ./assets/srt --title "小逻辑（句读版）" --author "句读小逻辑" --pdf
```

## 输入方式

支持五种输入方式：

```bash
# 目录扫描（非递归）
uv run subtitle-book --dir ./ep1 --dir ./ep2

# 直接指定文件
uv run subtitle-book --files ep1/01.srt --files ep1/02.srt

# glob 模式（支持递归）
uv run subtitle-book --pattern "**/*.srt"

# JSON 文件（保持指定顺序）
uv run subtitle-book --json chapters.json

# 混合使用
uv run subtitle-book --dir ./ep1 --files ep2/extra.srt --pattern "bonus/**/*.srt"
```

### JSON 格式

```json
["ep1/01.srt", "ep1/02.srt", "ep2/intro.srt"]
```

路径相对于 JSON 文件所在目录。**使用 JSON 输入时，章节顺序由文件列表决定，不会自动按集号排序。**

## 配置文件

编辑 `configs/default.yaml` 自定义文件名解析规则：

```yaml
book:
  title: "我的字幕书"
  author: "作者"

filename_pattern:
  # capture group 1 = 集号(数字)，capture group 2 = 标题
  # 集号为 0 或空表示序言/特殊章节，排在最前
  pattern: "^(?:第?(\\d+)[集话章篇]\\s*)?(.+)$"

encoding: "utf-8"
```

常用匹配示例：

| 文件名 | 集号 | 标题 |
|--------|------|------|
| `第10集本体论.srt` | 10 | 本体论 |
| `01.srt` | 0 | 01（无标记视为序言） |
| `序言.srt` | 0 | 序言 |

## 项目结构

```
src/
├── main.py              # CLI 入口
├── subtitle_book.py      # 主流程
├── models.py            # Chapter / Book 数据模型
├── parsers/
│   ├── srt.py           # SRT 解析（支持多种时间轴格式）
│   └── config.py        # 配置文件加载 + 正则匹配
├── generators/
│   ├── epub.py          # EPUB 生成（NCX + NAV 双重目录）
│   └── pdf.py           # PDF 生成（WeasyPrint 优先，Pandoc 备选）
configs/
└── default.yaml         # 默认配置
tests/                    # 单元测试
```

## SRT 时间轴格式

支持以下变体：

- `00:00:00,000 --> 00:00:00,000`（标准 SRT，逗号）
- `00:00:00.000 --> 00:00:00.000`（点号）
- `00:00:00 --> 00:00:00`（无毫秒）
- `0:00:00,000 --> 0:00:00,000`（省略小时前导零）

## 段落合并规则

- 相邻**相同文本**只保留一条
- 相邻字幕间隔 **< 500ms** 视为连续，合并为同一段落

## PDF 生成

| 方式 | 优点 | 缺点 |
|------|------|------|
| WeasyPrint | 功能完整，中文支持好 | 需要系统 GTK3/WebKit 依赖 |
| Pandoc + xelatex | 轻量，输出质量高 | 需要用户自行安装 LaTeX 环境 |

默认 WeasyPrint 优先，失败则回退 Pandoc。
