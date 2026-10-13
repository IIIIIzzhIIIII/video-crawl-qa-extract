"""基于 yt-dlp 的视频下载。

B 站的鉴权、WBI 签名、buvid 指纹、DASH 音视频合并等由 yt-dlp 负责处理，
我们只需提供 SESSDATA cookie 与 ffmpeg 路径，稳定性和成功率都远高于手写实现。
"""
import os
import subprocess
import sys

from config import FFMPEG_PATH, SESSDATA, TMP_DIR, VIDEO_DIR

FFMPEG_DIR = os.path.dirname(FFMPEG_PATH)
COOKIE_FILE = os.path.join(TMP_DIR, "cookies.txt")
# 远期过期时间（cookie 文件格式要求）
_EXPIRE = 1893456000


def write_cookie_file(sessdata: str = SESSDATA) -> str:
    """生成 yt-dlp 可用的 Netscape 格式 cookie 文件。"""
    os.makedirs(TMP_DIR, exist_ok=True)
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# Netscape HTTP Cookie File\n")
        f.write(f".bilibili.com\tTRUE\t/\tFALSE\t{_EXPIRE}\tSESSDATA\t{sessdata}\n")
    return COOKIE_FILE


def download_video(bvid: str, out_stem: str, timeout: int = 3600) -> str:
    """用 yt-dlp 下载指定 bvid 的视频（多分P 时仅下载第 1 个），返回 mp4 路径。"""
    cookie_file = write_cookie_file()
    out_template = os.path.join(VIDEO_DIR, f"{out_stem}.%(ext)s")
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--no-warnings",
        "--no-playlist",              # 多分P 只下第 1 个
        "-f", "bv*+ba/b",            # 最优视频 + 最优音频（DASH）
        "--merge-output-format", "mp4",
        "--ffmpeg-location", FFMPEG_DIR,
        "--cookies", cookie_file,
        "--referer", "https://www.bilibili.com",
        "-o", out_template,
        f"https://www.bilibili.com/video/{bvid}",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(f"yt-dlp 下载失败：\n{proc.stderr[-1500:]}")
    return os.path.join(VIDEO_DIR, f"{out_stem}.mp4")
