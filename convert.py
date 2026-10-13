"""一句指令：把视频（本地文件 或 B 站 BV 号）转成文字，可顺带提取答辩问答。

用法示例：
    python convert.py "E:\\录像\\决赛.mp4"                  # 只转文字
    python convert.py BV1L8ez6RELH                          # 自动下载后转文字
    python convert.py BV1L8ez6RELH --qa                     # 转文字 + 调 DeepSeek 提取问答
    python convert.py "E:\\录像\\决赛.mp4" --out "D:\\输出"   # 指定输出目录
    python convert.py "E:\\录像\\决赛.mp4" --device cpu       # 强制 CPU 推理
    python convert.py BV1L8ez6RELH --download-only          # 只下载视频，不转写

问答提取需要环境变量 LLM_API_KEY（DeepSeek 的 Key）；转写本身不需要 Key。
"""
import argparse
import glob
import os
import re
import sys

import config

BV_RE = re.compile(r"(BV[0-9A-Za-z]{10})")


def find_existing(bvid: str) -> str | None:
    """在视频目录里找已下载的同 BV 文件，避免重复下载。"""
    hits = sorted(glob.glob(os.path.join(config.VIDEO_DIR, f"*_{bvid}.mp4")))
    return hits[0] if hits else None


def download_bvid(bvid: str) -> tuple[str, str]:
    """下载指定 BV 号（复用阶段一的下载逻辑），返回 (mp4 路径, stem)。"""
    existing = find_existing(bvid)
    if existing:
        print(f"[复用] 本地已存在：{os.path.basename(existing)}")
        return existing, os.path.splitext(os.path.basename(existing))[0]

    from crawler import ytdlp
    from crawler.merge import sanitize_filename
    from crawler.playurl import get_video_info
    from crawler.session import BiliSession

    os.makedirs(config.VIDEO_DIR, exist_ok=True)
    session = BiliSession()
    info = get_video_info(session, bvid)
    title = info.get("title") or bvid
    stem = f"{sanitize_filename(title)}_{bvid}"
    print(f"[下载] {bvid} | {title}")
    return ytdlp.download_video(bvid, stem), stem


def resolve_target(target: str) -> tuple[str, str]:
    """把命令行输入解析为 (本地 mp4 路径, stem)。"""
    if os.path.isfile(target):
        path = os.path.abspath(target)
        return path, os.path.splitext(os.path.basename(path))[0]

    match = BV_RE.search(target)
    if not match:
        raise SystemExit(
            "无法识别输入，请传入本地视频路径，或形如 BV1L8ez6RELH 的 BV 号。\n"
            f"收到的是：{target}")
    return download_bvid(match.group(1))


def apply_overrides(args) -> None:
    """按命令行参数覆盖运行时配置（config 在各函数内部读取，改这里即生效）。"""
    if args.model:
        config.ASR_MODEL = args.model
    if args.device:
        config.ASR_DEVICE = args.device
    if args.out:
        base = os.path.abspath(args.out)
        config.ASR_DIR = base
        config.AUDIO_DIR = os.path.join(base, "audio")
        config.TRANSCRIPT_DIR = os.path.join(base, "transcripts")
        config.QA_DIR = os.path.join(base, "qa")
        config.ASR_STATE_FILE = os.path.join(base, "asr_state.json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="一条命令把视频转成文字（可顺带提取答辩问答）")
    parser.add_argument("target", help="本地视频文件路径，或 B 站 BV 号 / 视频链接")
    parser.add_argument("--qa", action="store_true",
                        help="转写后调用 DeepSeek 提取评委答辩问答")
    parser.add_argument("--out", default=None,
                        help="输出根目录（默认用 config 里的 data/asr）")
    parser.add_argument("--model", default=None,
                        help="faster-whisper 模型名（默认取 config.ASR_MODEL）")
    parser.add_argument("--device", default=None, choices=["cuda", "cpu"],
                        help="推理设备（默认取 config.ASR_DEVICE）")
    parser.add_argument("--force", action="store_true",
                        help="忽略已有结果，强制重跑")
    parser.add_argument("--download-only", action="store_true",
                        help="只下载视频，不转写（target 需为 BV 号 / 视频链接）")
    args = parser.parse_args(argv)

    apply_overrides(args)

    video_path, stem = resolve_target(args.target)
    print(f"[目标] {video_path}")

    if args.download_only:
        if os.path.isfile(args.target):
            print("\n[提示] 输入的是本地文件，无需下载。")
        else:
            print("\n[完成] 已下载，未转写。")
        return 0

    from asr import transcribe

    transcribe.transcribe_one(video_path, force=args.force, stem=stem)
    outs = transcribe.outputs_of(video_path, stem)
    print(f"\n[文字稿]\n  文本 {outs['txt']}\n  字幕 {outs['srt']}\n  明细 {outs['json']}")

    if not args.qa:
        return 0

    if not config.LLM_API_KEY:
        print("\n[问答] 未检测到 LLM_API_KEY，已跳过问答提取。设置示例："
              '\n         $env:LLM_API_KEY = "sk-xxxx"   # 然后重跑并加上 --qa')
        return 2

    from asr import extract_qa, llm

    print(f"\n[问答] 调用 {config.LLM_MODEL} 提取答辩问答 ...")
    try:
        result = extract_qa.extract_one(outs["json"], force=args.force)
    except llm.LLMError as exc:
        print(f"[问答] 调用失败：{exc}")
        return 3

    qa_md = os.path.join(config.QA_DIR, f"{stem}.qa.md")
    print(f"[问答] 共 {len(result.get('items') or [])} 条 -> {qa_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
