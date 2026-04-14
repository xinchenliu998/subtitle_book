# 项目开发指导

## 项目概述

SRT 字幕文件转 EPUB/PDF 电子书生成器，使用 Python 3.10+，uv 管理依赖。

## 开发规范

### 代码组织

- 单文件行数控制在 100-200 行以内，不超过 500 行
- 按功能划分目录：解析器在 `parsers/`、生成器在 `generators/`、数据模型在 `models.py`
- 使用 `uv` 管理依赖，pyproject.toml 为配置中心

### 测试

- 核心模块（解析器、模型）必须有单元测试
- 运行测试：`.venv/Scripts/python.exe -m pytest tests/ -v`
- `uv run pytest` 在本项目中有路径问题，请使用上述命令

### 运行方式

- **开发调试**：`uv run python -m src.subtitle_book --dir assets/srt`
- **直接运行**：`uv run subtitle-book --dir ./srt`
- **安装后运行**：`subtitle-book --dir ./srt`

### 构建

- editable 安装：`uv pip install -e .`
- 带 PDF 支持：`uv pip install -e ".[all]"`
- hatchling 打包配置在 `pyproject.toml` 的 `[tool.hatch.build.targets.wheel]` 中

## 目录结构

```
src/
├── main.py              # CLI 入口
├── subtitle_book.py      # 主流程编排
├── models.py            # Chapter / Book 数据模型
├── parsers/
│   ├── srt.py           # SRT 解析
│   └── config.py        # 配置加载
├── generators/
│   ├── epub.py          # EPUB 生成
│   └── pdf.py           # PDF 生成
configs/
└── default.yaml         # 默认配置
tests/                    # 单元测试
```
