"""视频搜索：调用带 WBI 签名的搜索接口，返回候选视频列表。"""
import re

from config import REQUEST_INTERVAL
from crawler.session import BiliSession

SEARCH_URL = "https://api.bilibili.com/x/web-interface/wbi/search/type"

_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    """去掉搜索标题里的 <em> 高亮标签。"""
    return _TAG_RE.sub("", text or "").strip()


def parse_duration(text) -> int:
    """把 "12:34" / "1:02:03" 形式的时长解析为秒。"""
    if isinstance(text, (int, float)):
        return int(text)
    if not text:
        return 0
    parts = str(text).split(":")
    try:
        nums = [int(p) for p in parts]
    except ValueError:
        return 0
    seconds = 0
    for n in nums:
        seconds = seconds * 60 + n
    return seconds


def search_videos(session: BiliSession, keyword: str, page: int = 1,
                  page_size: int = 30) -> list[dict]:
    """搜索视频，返回归一化后的候选列表。"""
    params = {
        "search_type": "video",
        "keyword": keyword,
        "page": page,
        "page_size": page_size,
    }
    signed = session.sign(params)
    data = session.get_json(SEARCH_URL, params=signed)
    if data.get("code") != 0:
        raise RuntimeError(f"搜索失败 code={data.get('code')} msg={data.get('message')}")

    results = data.get("data", {}).get("result") or []
    videos = []
    for item in results:
        if item.get("type") != "video":
            continue
        videos.append({
            "bvid": item.get("bvid"),
            "aid": item.get("aid"),
            "title": strip_html(item.get("title")),
            "author": item.get("author"),
            "play": item.get("play"),
            "duration": parse_duration(item.get("duration")),
            "description": strip_html(item.get("description", "")),
        })
    session.sleep(REQUEST_INTERVAL)
    return videos
