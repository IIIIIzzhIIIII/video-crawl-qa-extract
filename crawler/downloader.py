"""文件下载：支持断点续传与失败重试。"""
import os
import time

from config import MAX_RETRY, REFERER, TIMEOUT, USER_AGENT


def download_file(session, url: str, dest: str, max_retry: int = MAX_RETRY) -> str:
    """流式下载 url 到 dest，支持续传（.part 已存在时用 Range 续传）。"""
    last_err = None
    for attempt in range(1, max_retry + 1):
        try:
            existing = os.path.getsize(dest) if os.path.exists(dest) else 0
            headers = {"User-Agent": USER_AGENT, "Referer": REFERER}
            if existing:
                headers["Range"] = f"bytes={existing}-"
            resp = session.session.get(url, headers=headers, stream=True, timeout=TIMEOUT)
            resp.raise_for_status()
            # 服务端支持续传则追加，否则从头覆盖
            append = existing > 0 and resp.status_code == 206
            mode = "ab" if append else "wb"
            with open(dest, mode) as f:
                for chunk in resp.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        f.write(chunk)
            return dest
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            if attempt < max_retry:
                wait = 2 ** attempt
                print(f"    ! 下载出错（第 {attempt} 次）：{exc}，{wait}s 后重试")
                time.sleep(wait)
    raise RuntimeError(f"下载失败：{url}\n原因：{last_err}")
