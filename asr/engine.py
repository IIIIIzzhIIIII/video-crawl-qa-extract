"""加载 faster-whisper 模型。

Windows 上的坑：CTranslate2 走 GPU 需要 CUDA 12 的 cuBLAS / cuDNN 动态库，
而 pip 装的 `nvidia-cublas-cu12` / `nvidia-cudnn-cu12` 只把 DLL 放在
`site-packages/nvidia/*/bin`，并不会自动进入搜索路径。
所以这里必须在 `import faster_whisper` 之前把它们注册进去。
"""
import os
import site
import sys

import config

# ---------------------------------------------------------------- CUDA DLL


def _cuda_dll_dirs() -> list[str]:
    """找出 pip 安装的 nvidia-*-cu12 包中的 bin 目录。"""
    roots: list[str] = []
    try:
        roots.extend(site.getsitepackages())
    except AttributeError:
        pass
    try:
        roots.append(site.getusersitepackages())
    except AttributeError:
        pass
    roots.append(os.path.join(sys.prefix, "Lib", "site-packages"))

    dirs: list[str] = []
    for root in dict.fromkeys(roots):          # 去重且保持顺序
        nvidia = os.path.join(root, "nvidia")
        if not os.path.isdir(nvidia):
            continue
        for pkg in sorted(os.listdir(nvidia)):
            bin_dir = os.path.join(nvidia, pkg, "bin")
            if os.path.isdir(bin_dir):
                dirs.append(bin_dir)
    return dirs


def setup_cuda_dlls() -> list[str]:
    """把 CUDA DLL 目录加入 Windows 的 DLL 搜索路径。"""
    dirs = _cuda_dll_dirs()
    for d in dirs:
        try:
            os.add_dll_directory(d)
        except (AttributeError, OSError):
            pass
    if dirs:
        os.environ["PATH"] = os.pathsep.join(dirs + [os.environ.get("PATH", "")])
    return dirs


CUDA_DLL_DIRS = setup_cuda_dlls()

# 模型从国内镜像下载（直连 huggingface.co 基本超时）
os.environ.setdefault("HF_ENDPOINT", config.HF_ENDPOINT)
# 关掉 HuggingFace 的 Xet 传输后端：它不走镜像、直连 xethub，国内必然 401/超时
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
# 关掉 Windows 无符号链接权限的警告刷屏
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from faster_whisper import WhisperModel  # noqa: E402  —— 必须在 DLL 设置之后导入

from asr import compat  # noqa: E402,F401  打上 PyAV 兼容补丁（供 transcribe 解码用）

_MODEL: "WhisperModel | None" = None
_LOADED_AS: dict = {}


def cuda_device_count() -> int:
    """返回 CTranslate2 可见的 GPU 数量（0 表示只能跑 CPU）。"""
    try:
        import ctranslate2
        return int(ctranslate2.get_cuda_device_count())
    except Exception:  # noqa: BLE001
        return 0


def load_model(model_size: str | None = None,
               device: str | None = None,
               compute_type: str | None = None):
    """加载并缓存模型，返回 (model, 实际使用的配置)。

    GPU 加载失败时自动回落到 CPU（int8），保证流程不中断。
    """
    global _MODEL, _LOADED_AS
    if _MODEL is not None:
        return _MODEL

    model_size = model_size or config.ASR_MODEL
    device = device or config.ASR_DEVICE
    compute_type = compute_type or config.ASR_COMPUTE_TYPE
    os.makedirs(config.ASR_MODEL_DIR, exist_ok=True)

    attempts = [(device, compute_type)]
    if device != "cpu":
        attempts.append(("cpu", "int8"))

    last_error: Exception | None = None
    for dev, ctype in attempts:
        try:
            print(f"[ASR] 加载模型 {model_size} device={dev} compute_type={ctype} ...")
            _MODEL = WhisperModel(
                model_size,
                device=dev,
                compute_type=ctype,
                download_root=config.ASR_MODEL_DIR,
            )
            _LOADED_AS = {"model": model_size, "device": dev, "compute_type": ctype}
            print(f"[ASR] 加载完成：{_LOADED_AS}")
            return _MODEL
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            print(f"[ASR] 以 {dev}/{ctype} 加载失败：{exc}")

    raise RuntimeError(f"模型加载失败：{last_error}")


def loaded_as() -> dict:
    return dict(_LOADED_AS)
