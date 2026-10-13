"""下载元数据的管理（去重 / 记录下载状态）。"""
import json
import os
import time

from config import META_FILE


def load() -> dict:
    """读取 meta.json，不存在或损坏时返回空结构。"""
    if os.path.exists(META_FILE):
        try:
            with open(META_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"videos": {}}


def save(data: dict) -> None:
    """写回 meta.json。"""
    os.makedirs(os.path.dirname(META_FILE), exist_ok=True)
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_done(data: dict, bvid: str) -> bool:
    """该视频是否已成功下载过（用于去重）。"""
    rec = data.get("videos", {}).get(bvid)
    return bool(rec and rec.get("status") == "done")


def _record(data: dict, video: dict, status: str, **extra) -> None:
    rec = data.setdefault("videos", {}).setdefault(video["bvid"], {})
    rec.update({
        "bvid": video["bvid"],
        "title": video.get("title"),
        "author": video.get("author"),
        "duration": video.get("duration"),
        "play": video.get("play"),
        "status": status,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    })
    rec.update(extra)
    # 成功后清除历史错误信息，失败后清除历史路径，保持记录干净
    if status == "done":
        rec.pop("error", None)
    else:
        rec.pop("path", None)


def mark_done(data: dict, video: dict, path: str) -> None:
    _record(data, video, "done", path=path)


def mark_failed(data: dict, video: dict, error: str) -> None:
    _record(data, video, "failed", error=error)
