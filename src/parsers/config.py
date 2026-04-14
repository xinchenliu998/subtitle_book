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