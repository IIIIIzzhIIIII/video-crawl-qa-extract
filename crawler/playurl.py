"""视频详情 & 播放地址获取。"""
import time

from config import REQUEST_INTERVAL
from crawler.session import BiliSession

VIEW_URL = "https://api.bilibili.com/x/web-interface/view"
PLAYURL_URL = "https://api.bilibili.com/x/player/playurl"


def get_video_info(session: BiliSession, bvid: str) -> dict:
    """获取视频详情（含 cid 列表、标题、UP 主等）。"""
    data = session.get_json(VIEW_URL, params={"bvid": bvid})
    if data.get("code") != 0:
        raise RuntimeError(f"获取视频信息失败 bvid={bvid} code={data.get('code')}")
    return data["data"]


def get_playurl(session: BiliSession, bvid: str, cid: int,
                max_retry: int = 3) -> dict:
    """获取 DASH 播放地址（音视频分离）。

    注意：B 站 playurl 接口在请求过频时会返回 code=0 但音视频流为空，
    这里检测到空流会自动退避重试。
    """
    params = {
        "bvid": bvid,
        "cid": cid,
        "qn": 80,         # 请求 1080P，服务端按账号权限降级
        "fnval": 4048,    # DASH + HDR/4K/杜比/8K 等全部清晰度位（16 会拿不到流）
        "fnver": 0,
        "fourk": 1,
    }
    dash = {}
    for attempt in range(1, max_retry + 1):
        data = session.get_json(PLAYURL_URL, params=params)
        if data.get("code") != 0:
            raise RuntimeError(
                f"获取播放地址失败 bvid={bvid} cid={cid} code={data.get('code')}")
        dash = data.get("data", {})
        if dash.get("video") and dash.get("audio"):
            session.sleep(REQUEST_INTERVAL)
            return dash
        wait = 3 * attempt
        print(f"    ! 未拿到音视频流（疑似被限流），{wait}s 后重试 {attempt}/{max_retry}")
        time.sleep(wait)
    session.sleep(REQUEST_INTERVAL)
    return dash


def pick_streams(dash: dict, quality: int) -> tuple[dict, dict]:
    """从 dash 数据里挑选最合适的视频流与音频流。

    优先选择不超过 quality 的最高清晰度；若都不满足则退回最高可用清晰度。
    """
    videos = dash.get("video") or []
    audios = dash.get("audio") or []
    if not videos:
        raise RuntimeError("未获取到视频流（可能被风控限流，建议稍后重试或降低频率）")
    if not audios:
        raise RuntimeError("未获取到音频流")

    candidates = [v for v in videos if v.get("id", 0) <= quality] or videos
    best_video = max(candidates, key=lambda v: (v.get("id", 0), v.get("bandwidth", 0)))
    best_audio = max(audios, key=lambda a: a.get("bandwidth", 0))
    return best_video, best_audio
