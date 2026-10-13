"""调用 ffmpeg 合并音视频流。"""
import os
import subprocess

from config import FFMPEG_PATH


def sanitize_filename(name: str, max_len: int = 80) -> str:
    """把标题清洗为合法文件名。"""
    for ch in r'\/:*?"<>|':
        name = name.replace(ch, "_")
    name = name.strip().strip(".")
    return name[:max_len] or "video"


def merge(video_path: str, audio_path: str, output_path: str,
          ffmpeg: str = FFMPEG_PATH) -> str:
    """用 ffmpeg 无损合并视频流与音频流（-c copy）。"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cmd = [
        ffmpeg, "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c", "copy",
        "-loglevel", "error",
        output_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg 合并失败：\n{proc.stderr}")
    return output_path
