"""第三方库之间的兼容补丁。

目前只有一个：faster-whisper 调用 `av.open(..., metadata_errors="ignore")`，
但新版 PyAV（19.x）已经删掉了这个参数，会抛
`TypeError: open() got an unexpected keyword argument 'metadata_errors'`。
这里包一层，能传就传、不能传就丢掉（我们自己用 ffmpeg 生成的 wav 不会有坏元数据）。
"""
import av

_ORIG_OPEN = av.open


def _patched_open(file, mode: str = "r", **kwargs):
    metadata_errors = kwargs.pop("metadata_errors", None)
    if metadata_errors is not None:
        try:
            return _ORIG_OPEN(file, mode=mode, metadata_errors=metadata_errors, **kwargs)
        except TypeError:
            # 新版 PyAV：该参数已移除，降级为 FFmpeg 容器选项；再不行就忽略
            options = dict(kwargs.pop("options", None) or {})
            options.setdefault("metadata_errors", metadata_errors)
            try:
                return _ORIG_OPEN(file, mode=mode, options=options, **kwargs)
            except Exception:  # noqa: BLE001
                return _ORIG_OPEN(file, mode=mode, **kwargs)
    return _ORIG_OPEN(file, mode=mode, **kwargs)


def apply_all() -> None:
    """幂等地打上所有补丁。"""
    if getattr(av.open, "__name__", "") != "_patched_open":
        av.open = _patched_open


apply_all()
