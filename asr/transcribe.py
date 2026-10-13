"""批量把 data/videos 里的视频转成文字（txt / srt / json）。"""
import json
import os
import time

import config
from asr import audio, engine


def list_videos() -> list[str]:
    if not os.path.isdir(config.VIDEO_DIR):
        return []
    return sorted(
        os.path.join(config.VIDEO_DIR, name)
        for name in os.listdir(config.VIDEO_DIR)
        if name.lower().endswith(".mp4")
    )


def _fmt_ts(seconds: float) -> str:
    """秒 -> srt 时间戳 00:01:02,345"""
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _fmt_hms(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def load_state() -> dict:
    if os.path.exists(config.ASR_STATE_FILE):
        try:
            with open(config.ASR_STATE_FILE, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_state(state: dict) -> None:
    os.makedirs(config.ASR_DIR, exist_ok=True)
    with open(config.ASR_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def outputs_of(video_path: str, stem: str | None = None) -> dict:
    """计算某视频的产物路径；stem 可显式指定（便于处理任意输入文件）。"""
    stem = stem or os.path.splitext(os.path.basename(video_path))[0]
    return {
        "stem": stem,
        "txt": os.path.join(config.TRANSCRIPT_DIR, f"{stem}.txt"),
        "srt": os.path.join(config.TRANSCRIPT_DIR, f"{stem}.srt"),
        "json": os.path.join(config.TRANSCRIPT_DIR, f"{stem}.json"),
    }


def is_done(video_path: str, stem: str | None = None) -> bool:
    outs = outputs_of(video_path, stem)
    return all(os.path.exists(outs[k]) and os.path.getsize(outs[k]) > 0
               for k in ("txt", "srt", "json"))


def transcribe_one(video_path: str, force: bool = False,
                   stem: str | None = None) -> dict:
    """转写单个视频，写出 txt/srt/json，返回统计信息。

    stem 为 None 时按视频文件名推导；convert.py 等入口可显式传入。
    """
    outs = outputs_of(video_path, stem)
    stem = outs["stem"]

    if not force and is_done(video_path, stem):
        print(f"[跳过] 已转写：{stem}")
        return {"status": "skipped", "stem": stem}

    os.makedirs(config.TRANSCRIPT_DIR, exist_ok=True)

    print(f"[音频] 抽取中：{stem}")
    wav_path = audio.extract_audio(video_path)

    model = engine.load_model()
    print(f"[转写] 开始：{stem}（长音频会比较久，请耐心）")
    started = time.time()

    segments, info = model.transcribe(
        wav_path,
        language=config.ASR_LANGUAGE,
        beam_size=config.ASR_BEAM_SIZE,
        vad_filter=config.ASR_VAD,
        initial_prompt=config.ASR_INITIAL_PROMPT,
        condition_on_previous_text=False,   # 防止长音频陷入重复幻觉
        log_progress=config.ASR_VERBOSE,    # faster-whisper 1.2+ 用 log_progress 取代旧的 verbose
    )

    items: list[dict] = []
    txt_lines: list[str] = []
    srt_blocks: list[str] = []

    for i, seg in enumerate(segments, 1):
        text = (seg.text or "").strip()
        if not text:
            continue
        items.append({"start": round(seg.start, 2), "end": round(seg.end, 2), "text": text})
        txt_lines.append(text)
        srt_blocks.append(
            f"{len(items)}\n{_fmt_ts(seg.start)} --> {_fmt_ts(seg.end)}\n{text}\n"
        )
        if i % 100 == 0:
            print(f"    已处理 {i} 段 / 当前 {_fmt_hms(seg.end)}")

    with open(outs["txt"], "w", encoding="utf-8") as f:
        f.write("\n".join(txt_lines))
    with open(outs["srt"], "w", encoding="utf-8") as f:
        f.write("\n".join(srt_blocks))
    with open(outs["json"], "w", encoding="utf-8") as f:
        json.dump(
            {
                "video": os.path.basename(video_path),
                "duration": round(getattr(info, "duration", 0) or 0, 2),
                "language": getattr(info, "language", None),
                "language_probability": round(getattr(info, "language_probability", 0) or 0, 3),
                "model": engine.loaded_as(),
                "segments": items,
            },
            f, ensure_ascii=False, indent=2,
        )

    elapsed = time.time() - started
    duration = getattr(info, "duration", 0) or 0
    speed = (duration / elapsed) if elapsed > 0 else 0
    print(f"[转写] 完成：{stem} | {len(items)} 段 | 音频 {_fmt_hms(duration)} | "
          f"耗时 {_fmt_hms(elapsed)} | {speed:.1f}x 实时\n")

    return {
        "status": "done",
        "stem": stem,
        "segments": len(items),
        "duration": round(duration, 2),
        "elapsed": round(elapsed, 1),
        "speed": round(speed, 2),
        "model": engine.loaded_as(),
    }


def transcribe_all(force: bool = False, limit: int | None = None) -> None:
    videos = list_videos()
    if not videos:
        print(f"没找到视频，请先运行爬虫下载到 {config.VIDEO_DIR}")
        return

    state = load_state()
    todo = [v for v in videos if force or not is_done(v)]
    if limit is not None:
        todo = todo[:limit]

    print(f"共 {len(videos)} 个视频，待转写 {len(todo)} 个\n")
    os.makedirs(config.ASR_DIR, exist_ok=True)

    for idx, video in enumerate(todo, 1):
        stem = os.path.splitext(os.path.basename(video))[0]
        print(f"===== [{idx}/{len(todo)}] {stem} =====")
        try:
            result = transcribe_one(video, force=force)
            state[stem] = result
        except Exception as exc:  # noqa: BLE001
            print(f"[失败] {stem}：{exc}\n")
            state[stem] = {"status": "failed", "stem": stem, "error": str(exc)}
        save_state(state)

    done = sum(1 for v in state.values() if v.get("status") == "done")
    failed = [k for k, v in state.items() if v.get("status") == "failed"]
    print(f"转写结束：成功 {done} 个，失败 {len(failed)} 个")
    if failed:
        print("失败清单：" + "、".join(failed))
    print(f"结果目录：{config.TRANSCRIPT_DIR}")
