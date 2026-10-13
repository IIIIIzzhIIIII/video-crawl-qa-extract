"""记住上一次运行用过的配置，避免每次都要重新输入关键词。

优先级：命令行参数 > 上次记忆(data/run_config.json) > config.py 默认值。
"""
import json
import os

from config import DATA_DIR

STATE_FILE = os.path.join(DATA_DIR, "run_config.json")


def load() -> dict:
    """读取上次记忆的配置，文件不存在或损坏时返回空字典。"""
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save(state: dict) -> None:
    """把本次生效的配置写入记忆文件。"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def clear() -> bool:
    """删除记忆文件，返回是否真的删除了。"""
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
        return True
    return False
