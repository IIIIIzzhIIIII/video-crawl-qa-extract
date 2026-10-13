"""用 ffmpeg 从视频里抽出适合 ASR 的音频（16kHz 单声道 wav）。"""
import os
import subprocess

import config

SAMPLE_RATE = 16000


def extract_audio(video_path: str, out_dir: str | None = None, overwrite: bool = False) -> str:
    """抽取音频，返回 wav 路径。

    wav 体积约 32KB/s（18 小时 ≈ 2GB），转写完后可直接删掉 `data/asr/audio/`。
    """
    out_dir = out_dir or config.AUDIO_DIR
    os.makedirs(out_dir, exist_ok=True)

    stem = os.path.splitext(os.path.basename(video_path))[0]
    out_path = os.path.join(out_dir, f"{stem}.wav")

    if not overwrite and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        return out_path

    cmd = [
        config.FFMPEG_PATH, "-y", "-hide_banner", "-loglevel", "error",
        "-i", video_path,
        "-vn",                       # 丢掉视频轨
        "-ac", "1",                  # 单声道
        "-ar", str(SAMPLE_RATE),     # 16kHz
        "-c:a", "pcm_s16le",
        out_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0 or not os.path.exists(out_path):
        raise RuntimeError(f"抽出音频失败：{os.path.basename(video_path)}\n{proc.stderr}")
    return out_path
