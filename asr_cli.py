"""阶段二入口：本地 ASR 转写 + 云端 LLM 提取答辩问题。

用法：
    python asr_cli.py check                              # 检查 GPU / 依赖 / 配置
    python asr_cli.py transcribe [--force] [--limit N]   # 视频 -> 文字
    python asr_cli.py qa [--force] [--limit N]           # 文字 -> 问答
    python asr_cli.py summary                            # 跨视频汇总高频问题
    python asr_cli.py all [--force] [--limit N]          # 转写 + 问答 + 汇总
"""
import argparse
import os
import sys

import config


def cmd_check(_args) -> None:
    print("=== 环境检查 ===")
    print(f"Python      : {sys.version.split()[0]} ({sys.executable})")

    try:
        import faster_whisper
        print(f"faster-whisper: {faster_whisper.__version__}")
    except Exception as exc:  # noqa: BLE001
        print(f"faster-whisper: 未安装（{exc}）→ pip install -r requirements.txt")

    try:
        from asr import engine
        print(f"CUDA DLL 目录 : {engine.CUDA_DLL_DIRS or '未找到 nvidia-*-cu12 包'}")
        print(f"可见 GPU 数量 : {engine.cuda_device_count()}")
    except Exception as exc:  # noqa: BLE001
        print(f"CUDA 检测失败 : {exc}")

    print(f"ffmpeg        : {'存在' if os.path.exists(config.FFMPEG_PATH) else '不存在'} -> {config.FFMPEG_PATH}")
    print(f"ASR 模型      : {config.ASR_MODEL} / device={config.ASR_DEVICE} / compute={config.ASR_COMPUTE_TYPE}")

    videos = [n for n in os.listdir(config.VIDEO_DIR)] if os.path.isdir(config.VIDEO_DIR) else []
    videos = [n for n in videos if n.lower().endswith(".mp4")]
    transcripts = [n for n in os.listdir(config.TRANSCRIPT_DIR)] if os.path.isdir(config.TRANSCRIPT_DIR) else []
    transcripts = [n for n in transcripts if n.endswith(".json") and not n.startswith("_")]
    qa = [n for n in os.listdir(config.QA_DIR)] if os.path.isdir(config.QA_DIR) else []
    qa = [n for n in qa if n.endswith(".qa.json")]

    print(f"\n视频 {len(videos)} 个 | 已转写 {len(transcripts)} 个 | 已提取问答 {len(qa)} 个")
    print(f"LLM          : {config.LLM_BASE_URL} / {config.LLM_MODEL}")
    print(f"LLM_API_KEY  : {'已配置' if config.LLM_API_KEY else '未配置（设置环境变量 LLM_API_KEY）'}")


def cmd_transcribe(args) -> None:
    from asr import transcribe
    transcribe.transcribe_all(force=args.force, limit=args.limit)


def cmd_qa(args) -> None:
    from asr import extract_qa
    extract_qa.extract_all(force=args.force, limit=args.limit)


def cmd_summary(_args) -> None:
    from asr import extract_qa
    extract_qa.build_summary()


def cmd_all(args) -> None:
    from asr import extract_qa, transcribe
    transcribe.transcribe_all(force=args.force, limit=args.limit)
    extract_qa.extract_all(force=args.force, limit=args.limit)
    extract_qa.build_summary()


def main() -> None:
    parser = argparse.ArgumentParser(description="B 站路演视频 ASR 转写 + 答辩问题提取")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="检查环境、GPU 与配置")

    for name, help_text in (
        ("transcribe", "把视频转成文字"),
        ("qa", "从文字里提取评委答辩问答"),
        ("all", "转写 + 提取问答 + 汇总"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--force", action="store_true", help="忽略已有结果，强制重跑")
        p.add_argument("--limit", type=int, default=None, help="只处理前 N 个")

    sub.add_parser("summary", help="跨视频汇总答辩高频问题清单")

    args = parser.parse_args()
    {
        "check": cmd_check,
        "transcribe": cmd_transcribe,
        "qa": cmd_qa,
        "summary": cmd_summary,
        "all": cmd_all,
    }[args.command](args)


if __name__ == "__main__":
    main()
