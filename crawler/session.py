"""构造带 Cookie / 请求头 / WBI key 的 requests 会话。"""
import time

import requests

from config import REFERER, SESSDATA, TIMEOUT, USER_AGENT
from crawler.wbi import enc_wbi, extract_key_from_url

NAV_URL = "https://api.bilibili.com/x/web-interface/nav"
FINGER_URL = "https://api.bilibili.com/x/frontend/finger/spi"


class BiliSession:
    """封装 B 站会话，自动携带鉴权头、浏览器指纹与 WBI 签名能力。"""

    def __init__(self, sessdata: str = SESSDATA, user_agent: str = USER_AGENT,
                 referer: str = REFERER, timeout: int = TIMEOUT):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Referer": referer,
            "Origin": "https://www.bilibili.com",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })
        if sessdata:
            # SESSDATA 用 %2C 编码形式，requests 的 cookie jar 会原样发送
            self.session.cookies.set("SESSDATA", sessdata, domain=".bilibili.com")
        self._img_key = None
        self._sub_key = None
        self._init_buvid()

    # -------------------------------------------------- 基础请求
    def get_json(self, url: str, params: dict | None = None, headers: dict | None = None) -> dict:
        resp = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    # -------------------------------------------------- 浏览器指纹
    def _init_buvid(self) -> None:
        """获取 buvid3 / buvid4 指纹 cookie，降低被风控概率。"""
        try:
            data = self.get_json(FINGER_URL).get("data", {})
            if data.get("b_3"):
                self.session.cookies.set("buvid3", data["b_3"], domain=".bilibili.com")
            if data.get("b_4"):
                self.session.cookies.set("buvid4", data["b_4"], domain=".bilibili.com")
        except Exception:  # noqa: BLE001
            pass

    # -------------------------------------------------- WBI
    def refresh_wbi_keys(self) -> None:
        """从 nav 接口获取并缓存 wbi key。"""
        data = self.get_json(NAV_URL)
        wbi = data["data"]["wbi_img"]
        self._img_key = extract_key_from_url(wbi["img_url"])
        self._sub_key = extract_key_from_url(wbi["sub_url"])

    def sign(self, params: dict) -> dict:
        """对参数做 WBI 签名（首次调用会自动拉取 key）。"""
        if self._img_key is None or self._sub_key is None:
            self.refresh_wbi_keys()
        return enc_wbi(params, self._img_key, self._sub_key)

    # -------------------------------------------------- 状态
    def is_login(self) -> bool:
        try:
            return bool(self.get_json(NAV_URL)["data"]["isLogin"])
        except Exception:
            return False

    def sleep(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds)
