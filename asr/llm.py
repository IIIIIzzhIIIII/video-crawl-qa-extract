"""极简 OpenAI 兼容 Chat Completions 客户端。

只用 requests 实现，不引入 openai SDK，DeepSeek / 通义千问(DashScope 兼容模式) /
智谱 / Moonshot / OpenAI 都能直接对接，改 config.LLM_BASE_URL 即可。
"""
import time

import requests

import config


class LLMError(RuntimeError):
    pass


def _endpoint() -> str:
    return config.LLM_BASE_URL.rstrip("/") + "/chat/completions"


def chat(messages: list[dict],
         model: str | None = None,
         temperature: float | None = None,
         timeout: int | None = None,
         retry: int | None = None) -> str:
    """发一次对话请求，返回模型输出的文本内容。"""
    if not config.LLM_API_KEY:
        raise LLMError(
            "未配置 API Key。请先设置环境变量 LLM_API_KEY，例如：\n"
            '  $env:LLM_API_KEY="sk-xxxxxxxx"          # PowerShell，仅当前窗口有效\n'
            '  setx LLM_API_KEY "sk-xxxxxxxx"          # 永久写入，需要重开终端\n'
            "并确认 config.LLM_BASE_URL / LLM_MODEL 与你用的服务商匹配。"
        )

    payload = {
        "model": model or config.LLM_MODEL,
        "messages": messages,
        "temperature": config.LLM_TEMPERATURE if temperature is None else temperature,
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {config.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    timeout = timeout or config.LLM_TIMEOUT
    retry = config.LLM_RETRY if retry is None else retry

    last_error: Exception | None = None
    for attempt in range(1, retry + 1):
        try:
            resp = requests.post(_endpoint(), headers=headers, json=payload, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            # 429 / 5xx 值得重试，4xx 其它直接抛
            last_error = LLMError(f"HTTP {resp.status_code}: {resp.text[:300]}")
            if resp.status_code not in (429, 500, 502, 503, 504):
                raise last_error
        except requests.RequestException as exc:
            last_error = exc
        if attempt < retry:
            wait = 2 ** attempt
            print(f"    [LLM] 第 {attempt} 次失败（{last_error}），{wait}s 后重试 ...")
            time.sleep(wait)

    raise LLMError(f"LLM 调用失败（已重试 {retry} 次）：{last_error}")
