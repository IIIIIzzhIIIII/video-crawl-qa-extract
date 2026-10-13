"""B 站 WBI 签名算法。

B 站部分接口（搜索、播放地址 wbi 版等）要求请求携带 w_rid / wts 签名，
否则会被风控拒绝（返回 412）。签名流程：
  1. 从 nav 接口拿到 img_url / sub_url，取文件名（去掉扩展名）拼成 raw key；
  2. 用固定的置换表对 raw key 重排，取前 32 位得到 mixin_key；
  3. 参数按 key 排序 + 过滤特殊字符 + 拼上 wts 时间戳，做 URL 编码；
  4. md5(编码后的 query + mixin_key) 即 w_rid。
"""
import hashlib
import time
import urllib.parse

# 固定的置换表（B 站前端常量）
MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52,
]

# 编码时需要过滤掉的字符
_FILTER_CHARS = "!'()*"


def get_mixin_key(raw: str) -> str:
    """按置换表从原始 key 得到 32 位 mixin_key。"""
    return "".join(raw[i] for i in MIXIN_KEY_ENC_TAB)[:32]


def extract_key_from_url(url: str) -> str:
    """从 wbi 图片 URL 中取出文件名（不含扩展名）。"""
    return url.rsplit("/", 1)[-1].split(".")[0]


def enc_wbi(params: dict, img_key: str, sub_key: str) -> dict:
    """对参数做 WBI 签名，返回带 wts / w_rid 的新字典。"""
    mixin_key = get_mixin_key(img_key + sub_key)
    signed = {k: ("" if v is None else str(v)) for k, v in params.items()}
    signed["wts"] = str(int(time.time()))
    # 按 key 排序
    signed = dict(sorted(signed.items()))
    # 过滤特殊字符
    signed = {
        k: "".join(c for c in v if c not in _FILTER_CHARS)
        for k, v in signed.items()
    }
    query = urllib.parse.urlencode(signed)
    w_rid = hashlib.md5((query + mixin_key).encode("utf-8")).hexdigest()
    signed["w_rid"] = w_rid
    return signed
