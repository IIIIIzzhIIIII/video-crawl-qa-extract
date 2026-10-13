"""
全局配置。

本文件是「默认配置」，不含任何私密信息，可以安全分享。
自己的 SESSDATA / ffmpeg 路径 / LLM_API_KEY 请写在 config_local.py（已被 .gitignore 忽略），
该文件会在本文件末尾被自动导入并覆盖同名配置。
"""
import os

# ---------------------------------------------------------------- 路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
VIDEO_DIR = os.path.join(DATA_DIR, "videos")     # 成品 mp4
TMP_DIR = os.path.join(DATA_DIR, "tmp")          # 下载中的分片文件
META_FILE = os.path.join(DATA_DIR, "meta.json")  # 元数据 / 下载状态

# ---------------------------------------------------------------- 凭证
# B 站登录 Cookie 中的 SESSDATA（私密信息，请勿提交到仓库；逗号要写成 %2C）。
# 请填在 config_local.py（已被 .gitignore 忽略），或用环境变量 BILI_SESSDATA 传入。
SESSDATA = os.environ.get("BILI_SESSDATA", "")

# ---------------------------------------------------------------- ffmpeg
# 默认按 PATH 里的 ffmpeg 调用；若未加入 PATH，请在 config_local.py 里写全路径。
FFMPEG_PATH = os.environ.get("BILI_FFMPEG", "ffmpeg")

# ---------------------------------------------------------------- 请求头
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
REFERER = "https://www.bilibili.com"

# ---------------------------------------------------------------- 抓取控制
KEYWORDS = ["创新创业大赛 国赛 路演 答辩"]  # 搜索关键词（可多个）
PAGES_PER_KEYWORD = 1                       # 每个关键词抓取页数
REQUEST_INTERVAL = 1.5                      # 每次请求间隔（秒），防风控
MAX_RETRY = 3                               # 失败重试次数
TIMEOUT = 30                                # 请求超时（秒）

# 下载控制
MAX_DOWNLOAD = 1        # 本次最多下载多少个视频（-1 表示不限）
MIN_DURATION = 0        # 最短时长（秒），0 表示不限
MAX_DURATION = 0        # 最长时长（秒），0 表示不限（用户要求不限时长）
QUALITY = 80            # 清晰度：80=1080P, 64=720P, 32=480P, 16=360P

# ================================================================ 阶段二：ASR 转写
ASR_DIR = os.path.join(DATA_DIR, "asr")                     # ASR 阶段所有产物
AUDIO_DIR = os.path.join(ASR_DIR, "audio")                  # ffmpeg 抽出的 wav
TRANSCRIPT_DIR = os.path.join(ASR_DIR, "transcripts")       # 转写结果 txt/srt/json
QA_DIR = os.path.join(ASR_DIR, "qa")                        # 答辩问题提取结果
ASR_STATE_FILE = os.path.join(ASR_DIR, "asr_state.json")    # 转写进度
ASR_MODEL_DIR = os.path.join(ASR_DIR, "models")             # 模型缓存（放 E 盘，别塞 C 盘）

ASR_MODEL = os.environ.get("ASR_MODEL", "large-v3-turbo")   # large-v3-turbo：速度/中文准确率最佳平衡
ASR_DEVICE = os.environ.get("ASR_DEVICE", "cuda")                   # cuda / cpu
ASR_COMPUTE_TYPE = os.environ.get("ASR_COMPUTE_TYPE", "int8_float16")  # GPU 用 int8_float16；CPU 用 int8
ASR_LANGUAGE = "zh"                                                 # 固定中文，避免误判
ASR_BEAM_SIZE = 5                                                   # 束搜索宽度
ASR_VAD = True                                                      # 开启 VAD 跳过静音
ASR_VERBOSE = False                                                 # 是否打印每段进度
# 领域词提示：把大赛专有名词喂给模型，能明显减少同音错字
ASR_INITIAL_PROMPT = (
    "以下是中国国际大学生创新创业大赛（原互联网+大赛）的路演答辩现场录音。"
    "涉及环节：项目陈述、评委提问、选手答辩、打分点评。"
    "常见词汇：高教主赛道、红旅赛道、职教赛道、产业命题赛道、国际项目、"
    "国赛、省赛、金奖、银奖、冠军争夺赛、商业计划书、核心竞争力、技术壁垒、"
    "商业模式、落地场景、知识产权、股权结构、营收、毛利率、市场规模、"
    "第一曲线、第二曲线、乡村振兴、双碳、国产替代。"
)
# HuggingFace 国内镜像（直连 huggingface.co 基本下不动模型）
HF_ENDPOINT = os.environ.get("HF_ENDPOINT", "https://hf-mirror.com")

# ================================================================ 阶段二：答辩问题提取（云端 LLM）
# 走 OpenAI 兼容协议，DeepSeek / 通义千问(DashScope) / 智谱 / OpenAI 均可
#   DeepSeek:  LLM_BASE_URL=https://api.deepseek.com/v1        LLM_MODEL=deepseek-chat
#   通义千问:  LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1  LLM_MODEL=qwen-plus
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")          # 用环境变量传入，勿写死在文件里
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")
LLM_TEMPERATURE = 0.2
LLM_TIMEOUT = 300          # 单次请求超时（秒），长文本抽取较慢
LLM_RETRY = 3              # 失败重试次数
LLM_CHUNK_CHARS = 5000     # 每次送进模型的转写文本长度（按段落边界切）

# ================================================================ 本地私密配置
# config_local.py 用来放自己的 SESSDATA / ffmpeg 路径 / LLM_API_KEY 等，
# 该文件已被 .gitignore 忽略（不会被提交、也不会随分发包带出去）。
# 首次使用请复制 config_local.example.py 为 config_local.py 并填写。
try:
    from config_local import *  # noqa: F401,F403
except ImportError:
    pass

# 环境变量优先级最高，便于临时覆盖 config_local.py 里的设置
if os.environ.get("BILI_SESSDATA"):
    SESSDATA = os.environ["BILI_SESSDATA"]
if os.environ.get("BILI_FFMPEG"):
    FFMPEG_PATH = os.environ["BILI_FFMPEG"]
if os.environ.get("LLM_API_KEY"):
    LLM_API_KEY = os.environ["LLM_API_KEY"]
