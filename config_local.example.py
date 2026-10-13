"""本地私密配置模板（示例）。

用法：把本文件复制一份，改名为 config_local.py，填入自己的值即可。
config_local.py 已被 .gitignore 忽略，不会被提交，也不会随分发包一起给别人。

这里写的值会自动覆盖 config.py 里的同名默认配置。
三项必填：SESSDATA、LLM_API_KEY、FFMPEG_PATH（若 ffmpeg 已在 PATH 中可不填最后一项）。
"""

# ---- 1) B 站登录凭证（必填）-------------------------------------------------
# 获取方法：浏览器登录 bilibili.com -> F12 -> Application/应用程序 -> Cookies
#          -> https://www.bilibili.com -> 找到 SESSDATA，复制它的值。
# 注意：值里的逗号必须写成 %2C（浏览器里复制出来通常已经是 %2C，若看到裸逗号请手动替换）。
SESSDATA = "在这里粘贴你的 SESSDATA"

# ---- 2) ffmpeg 路径（若 ffmpeg 已加入系统 PATH，可整行删掉或留空）-----------
# 例：FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"
FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"

# ---- 3) 云端大模型（必填，用于把文字提取成答辩问答）-------------------------
# DeepSeek 申请地址：https://platform.deepseek.com/  （充一点点钱即可，很便宜）
# 也可换成其它 OpenAI 兼容服务，例如通义千问：
#   LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
#   LLM_MODEL    = "qwen-plus"
LLM_API_KEY = "sk-在这里粘贴你的Key"
LLM_BASE_URL = "https://api.deepseek.com/v1"
LLM_MODEL = "deepseek-chat"

# ---- 可选：本地语音识别设置 -------------------------------------------------
# ASR_MODEL = "large-v3-turbo"   # 想要更准可改 "large-v3"（慢约 3 倍）；更快可用 "small"（中文错字偏多）
# ASR_DEVICE = "cuda"            # 没有 NVIDIA 显卡请改成 "cpu"（会慢很多）
# ASR_COMPUTE_TYPE = "int8_float16"   # CPU 时建议改成 "int8"
