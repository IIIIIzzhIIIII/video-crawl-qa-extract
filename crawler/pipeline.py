"""流水线编排：搜索 → 过滤 → 去重 → 下载 → 合并 → 记录。"""
import os

import config
from crawler import meta, ytdlp
from crawler.merge import sanitize_filename
from crawler.playurl import get_video_info
from crawler.search import search_videos
from crawler.session import BiliSession


def collect_candidates(session: BiliSession) -> list[dict]:
    """按所有关键词搜索并去重，返回候选视频列表。"""
    seen: set[str] = set()
    candidates: list[dict] = []
    for kw in config.KEYWORDS:
        for page in range(1, config.PAGES_PER_KEYWORD + 1):
            print(f"[搜索] 关键词='{kw}' 第 {page} 页 ...")
            try:
                vids = search_videos(session, kw, page=page)
            except Exception as exc:  # noqa: BLE001
                print(f"  ! 搜索失败：{exc}")
                continue
            for v in vids:
                bvid = v.get("bvid")
                if not bvid or bvid in seen:
                    continue
                seen.add(bvid)
                candidates.append(v)
    return candidates


def in_duration_range(seconds: int) -> bool:
    if config.MIN_DURATION and seconds < config.MIN_DURATION:
        return False
    if config.MAX_DURATION and seconds > config.MAX_DURATION:
        return False
    return True


def download_one(session: BiliSession, video: dict) -> str:
    """获取视频信息并用 yt-dlp 下载（多分P 仅下第 1 个），返回成品 mp4 路径。"""
    bvid = video["bvid"]
    info = get_video_info(session, bvid)
    title = info.get("title") or video.get("title") or bvid
    pages = info.get("pages") or []
    if len(pages) > 1:
        print(f"  提示：该视频共 {len(pages)} 个分P，本次仅下载第 1 个")

    out_stem = f"{sanitize_filename(title)}_{bvid}"
    return ytdlp.download_video(bvid, out_stem)


def run(dry_run: bool = False) -> None:
    os.makedirs(config.VIDEO_DIR, exist_ok=True)
    os.makedirs(config.TMP_DIR, exist_ok=True)

    session = BiliSession()
    print("登录状态:", session.is_login())

    meta_data = meta.load()
    candidates = collect_candidates(session)
    filtered = [v for v in candidates if in_duration_range(v.get("duration", 0))]
    print(f"共获得候选视频 {len(candidates)} 个，时长过滤后 {len(filtered)} 个\n")

    if dry_run:
        for i, v in enumerate(filtered, 1):
            flag = "已下载" if meta.is_done(meta_data, v["bvid"]) else "待下载"
            print(f"{i:>2}. [{flag}] {v['bvid']} {v.get('duration', 0):>5}s "
                  f"{str(v.get('title', ''))[:45]}")
        print(f"\n[dry-run] 仅预览，未下载任何视频（当前记忆的关键词见上方 [配置] 行）")
        return

    downloaded = 0
    for v in filtered:
        if config.MAX_DOWNLOAD >= 0 and downloaded >= config.MAX_DOWNLOAD:
            break
        if meta.is_done(meta_data, v["bvid"]):
            print(f"[跳过] 已下载过 {v['bvid']}")
            continue
        print(f"[下载] {v['bvid']} | {v.get('title', '')[:50]}")
        try:
            path = download_one(session, v)
            meta.mark_done(meta_data, v, path)
            downloaded += 1
            print(f"  ✓ 完成：{path}\n")
        except Exception as exc:  # noqa: BLE001
            print(f"  ✗ 失败 {v['bvid']}：{exc}\n")
            meta.mark_failed(meta_data, v, str(exc))
        meta.save(meta_data)

    print(f"本次共下载 {downloaded} 个视频，输出目录：{config.VIDEO_DIR}")
