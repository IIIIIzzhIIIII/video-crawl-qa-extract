# B 站路演视频采集 · 转写 · 答辩问答提取

批量采集「创新创业大赛 / 国赛 / 路演 / 答辩」类视频，并**转成文字、提取评委答辩问答**。

- **阶段一**：搜索 + 下载 B 站视频（见下文「阶段一」）
- **阶段二**：本地 ASR 转写 + 云端大模型提取答辩问答（见下文「阶段二」）

> 给非技术用户看的完整图文说明，见 **[使用说明.md](使用说明.md)**。

## 三步上手（Windows）

1. **装 Python**（3.10+）：<https://www.python.org/downloads/>，安装时务必勾选 `Add python.exe to PATH`
2. **双击 `setup.bat`**：自动建环境、装依赖（首次几分钟；若当前 Python 已装好依赖会自动跳过）
3. **填 `config_local.py`**：用记事本打开，填好三项 —— B 站 `SESSDATA`、`LLM_API_KEY`、`FFMPEG_PATH`

之后**双击 `run.bat`** 按菜单选即可，也可以在终端里直接跑命令：

```bash
python asr_cli.py all                # 一条龙：已有视频 -> 文字稿 -> 答辩问答 -> 高频清单
python convert.py BV1L8ez6RELH --qa  # 单个视频（BV 号 / 本地文件路径）-> 文字 + 问答
```

## 功能

- 关键词搜索 B 站视频（带 **WBI 签名**，需登录 Cookie，否则被风控返回 412）
- 支持时长过滤、多关键词、多页抓取
- 用 **yt-dlp** 下载（自动处理 B 站鉴权、buvid 指纹、DASH 音视频合并），输出 mp4
- **元数据去重**：`data/meta.json` 记录已下载视频，重复运行自动跳过
- 多分P 视频默认只下载第 1 个分P

## 目录结构

```
├── config.py              # 默认配置（不含任何私密信息，可安全分享）
├── config_local.example.py # 私密配置模板（复制成 config_local.py 后填自己的值）
├── config_local.py        # 【本机私密配置】SESSDATA / ffmpeg / API Key（已被 .gitignore 忽略）
├── setup.bat              # 一键安装（建环境、装依赖、生成配置）
├── run.bat                # 一键使用（双击出菜单）
├── main.py                # 阶段一入口：搜索 + 下载
├── convert.py             # 阶段二入口：单个视频/链接 -> 文字（可加 --qa 出问答）
├── requirements.txt
├── crawler/
│   ├── wbi.py             # WBI 签名算法
│   ├── session.py         # 带 Cookie / 浏览器指纹 / WBI 能力的会话
│   ├── search.py          # 关键词搜索
│   ├── playurl.py         # 视频详情（含原生取流方案，作为备用）
│   ├── downloader.py      # 原生分片下载（备用，主链路未启用）
│   ├── merge.py           # ffmpeg 合并 + 文件名清洗
│   ├── ytdlp.py           # yt-dlp 下载封装（主链路）
│   ├── meta.py            # 元数据 / 去重 / 状态记录
│   ├── runstate.py        # 记忆上次运行的关键词等配置
│   └── pipeline.py        # 流水线编排
├── asr_cli.py             # 阶段二入口（转写 / 问答提取 / 汇总）
├── asr/
│   ├── audio.py           # ffmpeg 抽取 16kHz 单声道音频
│   ├── compat.py          # 兼容补丁（PyAV 版本差异）
│   ├── engine.py          # 加载 faster-whisper（含 Windows CUDA DLL 处理）
│   ├── transcribe.py      # 批量转写，输出 txt/srt/json（增量续跑）
│   ├── llm.py             # OpenAI 兼容的云端大模型客户端
│   ├── prompts.py         # 提示词模板
│   └── extract_qa.py      # 抽取答辩问答 + 跨视频汇总
└── data/
    ├── videos/            # 成品 mp4
    ├── tmp/               # 临时文件（cookie 等）
    ├── asr/               # 阶段二产物（audio / models / transcripts / qa）
    └── meta.json          # 下载元数据
```

## 环境要求

- Python 3.10+
- ffmpeg（`config.FFMPEG_PATH` 指向 `ffmpeg.exe`）
- 依赖安装：`pip install -r requirements.txt`

## 配置说明（config.py）

| 配置项 | 说明 |
| --- | --- |
| `SESSDATA` | B 站登录凭证，**逗号必须写成 `%2C`**；可用环境变量 `BILI_SESSDATA` 覆盖 |
| `FFMPEG_PATH` | ffmpeg.exe 全路径（也可用环境变量 `BILI_FFMPEG` 覆盖） |
| `KEYWORDS` | 搜索关键词列表 |
| `PAGES_PER_KEYWORD` | 每个关键词抓取页数 |
| `MAX_DOWNLOAD` | 最多下载数量，`-1` 为不限 |
| `MIN_DURATION` / `MAX_DURATION` | 时长过滤（秒），`0` 为不限 |
| `REQUEST_INTERVAL` | 请求间隔（秒），防风控 |

## 用法

```bash
# 沿用上次用的关键词（首次运行时为 config.py 默认值）
python main.py

# 指定关键词，只下载 1 个；这个关键词会被记住，下次不加 -k 也用它
python main.py -k "中国国际大学生创新创业大赛 路演 2025年" -m 1

# 多关键词、抓 2 页、最多下 3 个
python main.py -k "互联网+ 国赛 路演" -k "创新创业 答辩" -p 2 -m 3

# 只搜索、列出候选（含"已下载/待下载"标记），不下载
python main.py --dry-run

# 清除记忆，恢复 config.py 默认值
python main.py --reset
```

### 参数优先级与"记忆"机制

优先级：**命令行参数 > 上次运行的记忆 > `config.py` 默认值**

- 不加任何参数时，会沿用上一次的 `关键词 / 页数 / 最多下载 / 清晰度`，
  而不是回落到 `config.py` 的默认关键词（这是很多人踩的坑）。
- 记忆保存在 `data/run_config.json`，每次运行都会打印生效配置，例如：
  `[配置] 关键词=['...'] 页数=2 最多下载=1 清晰度=80`
- 想换关键词 → 再加一次 `-k`；想彻底恢复默认 → `python main.py --reset`。
- 想固定某个默认值（不依赖记忆）→ 直接改 `config.py` 里的 `KEYWORDS` 等。

## 注意事项

- `SESSDATA` 属敏感信息，请填在 `config_local.py`（`.gitignore` 已忽略），不要写进 `config.py`。
- 非大会员账号最高 **1080P**；ASR 仅依赖音频，画质足够。
- B 站对接口有频率限制，请勿把 `REQUEST_INTERVAL` 调得过低。

---

# 阶段二：ASR 转写 + 答辩问题提取

把已下载的视频变成**带时间戳的文字稿**，再从里面抽出**评委提问 + 选手答辩**，最后汇总成**高频答辩问题清单**。

## 路线

- **ASR**：本地 `faster-whisper large-v3-turbo`（CTranslate2 / GPU），免费、数据不出本机
- **问答提取**：云端大模型（OpenAI 兼容协议：DeepSeek / 通义千问 / 智谱 / OpenAI）

## 安装

最简单是**双击 `setup.bat`**（自动建虚拟环境、装依赖、生成 `config_local.py`）。
手动安装也行：

```bash
pip install -r requirements.txt
```

Windows 上 CTranslate2 走 GPU 需要 CUDA 12 的 **cuBLAS**，所以 `requirements.txt` 里带了
`nvidia-cublas-cu12`（约 550MB）。代码会自动把它的 DLL 目录注册进搜索路径，无需手动配 PATH。
**不需要**再装 `nvidia-cudnn-cu12`（CTranslate2 自带 `cudnn64_9.dll`）。

## 配置（config_local.py）

**推荐做法**：把 `config_local.example.py` 复制成 `config_local.py`（`setup.bat` 会自动生成），
填好三项即可，无需设环境变量：

| 配置项 | 说明 |
| --- | --- |
| `SESSDATA` | B 站登录凭证，**逗号必须写成 `%2C`** |
| `FFMPEG_PATH` | `ffmpeg.exe` 全路径（若 ffmpeg 已在 PATH 中可不填） |
| `LLM_API_KEY` | 云端大模型 Key（默认 DeepSeek：<https://platform.deepseek.com>） |

`config_local.py` 已被 `.gitignore` 忽略，**不会**被提交、也**不会**随分发包带出去。

也可以用环境变量临时覆盖（**优先级高于 `config_local.py`**）：

```powershell
$env:LLM_API_KEY="sk-xxxxxxxx"       # 仅当前终端有效
$env:BILI_SESSDATA="xxxx%2Cxxxx"     # 临时换 B 站账号
setx LLM_API_KEY "sk-xxxxxxxx"       # 永久生效，需重开终端

# 想换服务商（默认 DeepSeek）：
$env:LLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:LLM_MODEL="qwen-plus"
```

## 用法

```bash
python asr_cli.py check          # 自检：GPU / 依赖 / ffmpeg / API Key / 数据统计
python asr_cli.py transcribe     # 视频 -> 文字稿
python asr_cli.py qa             # 文字稿 -> 答辩问答
python asr_cli.py summary        # 跨视频汇总高频问题
python asr_cli.py all            # 一条龙：转写 + 问答 + 汇总

python convert.py BV1L8ez6RELH --qa            # 单个视频（BV 号 / 本地文件）-> 文字 + 问答
python convert.py BV1L8ez6RELH --download-only # 只下载视频，不转写
```

通用参数：`--limit N` 只处理前 N 个，`--force` 忽略已有结果强制重跑。
`convert.py` 另有 `--out 目录` / `--model` / `--device`（`cuda`|`cpu`）/ `--download-only`（只下载不转写）。
不方便敲命令时，直接**双击 `run.bat`** 按菜单操作即可。

## 产物

```
data/asr/
├── audio/           # 16kHz 单声道 wav（转写完可删，省空间）
├── models/          # faster-whisper 模型缓存（放 E 盘，不占 C 盘）
├── transcripts/     # <视频名>.txt / .srt / .json（json 带时间戳，供问答定位）
├── qa/              # <视频名>.qa.md / .qa.json
│                    #   _all_questions.json     全部问题汇总
│                    #   _高频答辩问题清单.md   最终成果
└── asr_state.json   # 转写进度（支持断点续跑）
```

## 说明与注意

- 默认模型 `large-v3-turbo`：本机实测 **13.3x 实时**，18.5 小时音频约 **1.4 小时** 转完。
  想更准可换 `ASR_MODEL=large-v3`（约 3 倍慢、质量略高）；更快可换 `small`（但中文错字明显变多）。
- 中断后重跑会自动跳过已完成的，支持断点续跑。
- GPU 加载失败会**自动回落 CPU(int8)**，但速度会慢十几倍，建议先 `check` 确认 GPU 可用。
- 长视频按约 5000 字切块送模型，逐块抽取再合并；每条问答都带时间戳，方便回原视频核对。
- 问答与汇总均为模型生成，**关键数据（金额、比例、分数）建议对照 `.srt` 复核**。

## 分享给别人

1. **打包时不要带上**：`config_local.py`（含你的 B 站 cookie 和 API Key）、`data/`（含你的视频和产物）。
2. 对方拿到后：装 Python → 双击 `setup.bat` → 填自己的 `config_local.py` → 双击 `run.bat`。
3. 对方需要自备：B 站账号的 `SESSDATA`、自己的 `LLM_API_KEY`、ffmpeg。
4. 对方**没有 NVIDIA 显卡也能跑**，只会回落到 CPU 推理、速度慢很多
   （可在其 `config_local.py` 里设 `ASR_DEVICE = "cpu"`、`ASR_COMPUTE_TYPE = "int8"`）。
5. 首次运行会自动从国内镜像下载 whisper 模型（约 1.6GB），需要联网。
