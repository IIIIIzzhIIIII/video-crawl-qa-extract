"""调云端 LLM，从转写文本里抽取评委提问与选手答辩内容。"""
import json
import os
import re

import config
from asr import llm, prompts

_JSON_RE = re.compile(r"\{.*\}", re.S)


def _fmt_hms(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _esc(text: str) -> str:
    """转义 markdown 表格里的竖线和换行。"""
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def list_transcripts() -> list[str]:
    if not os.path.isdir(config.TRANSCRIPT_DIR):
        return []
    return sorted(
        os.path.join(config.TRANSCRIPT_DIR, name)
        for name in os.listdir(config.TRANSCRIPT_DIR)
        if name.endswith(".json") and not name.startswith("_")
    )


def build_chunks(segments: list[dict], max_chars: int | None = None) -> list[dict]:
    """把带时间戳的分段按字数切成若干块，切点尽量落在句段边界。"""
    max_chars = max_chars or config.LLM_CHUNK_CHARS
    chunks: list[dict] = []
    cur_lines: list[str] = []
    cur_chars = 0
    start_ts: float | None = None

    for seg in segments:
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        start = float(seg.get("start", 0))
        line = f"[{_fmt_hms(start)}] {text}"
        if start_ts is None:
            start_ts = start
        if cur_lines and cur_chars + len(line) > max_chars:
            chunks.append({
                "start": _fmt_hms(start_ts),
                "end": _fmt_hms(start),
                "content": "\n".join(cur_lines),
            })
            cur_lines, cur_chars, start_ts = [], 0, start
        cur_lines.append(line)
        cur_chars += len(line) + 1

    if cur_lines:
        last_end = float(segments[-1].get("end", 0)) if segments else (start_ts or 0)
        chunks.append({
            "start": _fmt_hms(start_ts or 0),
            "end": _fmt_hms(last_end),
            "content": "\n".join(cur_lines),
        })
    return chunks


def parse_json(raw: str) -> dict:
    """从模型输出里抠出 JSON（容忍 ```json 包裹和前后废话）。"""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    match = _JSON_RE.search(text)
    if not match:
        raise ValueError("模型输出中未找到 JSON")
    return json.loads(match.group(0))


def extract_one(json_path: str, force: bool = False) -> dict:
    """抽取单个视频的问答，写出 <stem>.qa.json / <stem>.qa.md。"""
    stem = os.path.splitext(os.path.basename(json_path))[0]
    out_json = os.path.join(config.QA_DIR, f"{stem}.qa.json")
    out_md = os.path.join(config.QA_DIR, f"{stem}.qa.md")

    if not force and os.path.exists(out_json) and os.path.getsize(out_json) > 0:
        print(f"[跳过] 已提取：{stem}")
        with open(out_json, encoding="utf-8") as f:
            return json.load(f)

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    segments = data.get("segments") or []
    if not segments:
        print(f"[跳过] 无转写内容：{stem}")
        return {"video": data.get("video"), "stem": stem, "project": "", "items": []}

    chunks = build_chunks(segments)
    print(f"[提取] {stem} | {len(segments)} 段 -> {len(chunks)} 块")

    all_items: list[dict] = []
    project = ""
    for i, ch in enumerate(chunks, 1):
        print(f"  ({i}/{len(chunks)}) {ch['start']} ~ {ch['end']}")
        user = prompts.QA_USER_TEMPLATE.format(
            title=stem, chunk_index=f"{i}/{len(chunks)}",
            start=ch["start"], end=ch["end"], content=ch["content"],
        )
        raw = llm.chat([
            {"role": "system", "content": prompts.QA_SYSTEM},
            {"role": "user", "content": user},
        ])
        try:
            obj = parse_json(raw)
        except Exception as exc:  # noqa: BLE001
            print(f"    ! 该块解析失败，已跳过：{exc}")
            continue
        if not project and obj.get("project"):
            project = str(obj["project"]).strip()
        for item in obj.get("items") or []:
            question = str(item.get("question", "")).strip()
            if not question:
                continue
            all_items.append({
                "time": str(item.get("time", "")).strip() or ch["start"],
                "question": question,
                "answer": str(item.get("answer", "")).strip(),
                "category": str(item.get("category", "")).strip() or "其他",
            })

    result = {"video": data.get("video"), "stem": stem, "project": project, "items": all_items}

    os.makedirs(config.QA_DIR, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    lines = [
        f"# {stem}",
        "",
        f"- 项目：{project or '未识别'}",
        f"- 问答条数：{len(all_items)}",
        "",
        "| # | 时间 | 类别 | 评委提问 | 回答要点 |",
        "|---|---|---|---|---|",
    ]
    for i, item in enumerate(all_items, 1):
        lines.append(
            f"| {i} | {item['time']} | {item['category']} | "
            f"{_esc(item['question'])} | {_esc(item['answer'])} |"
        )
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"[提取] 完成：{stem} | {len(all_items)} 条问答\n")
    return result


def _all_qa_files() -> list[str]:
    if not os.path.isdir(config.QA_DIR):
        return []
    return sorted(
        os.path.join(config.QA_DIR, n)
        for n in os.listdir(config.QA_DIR)
        if n.endswith(".qa.json")
    )


def extract_all(force: bool = False, limit: int | None = None) -> None:
    transcripts = list_transcripts()
    if not transcripts:
        print(f"没找到转写结果，请先运行：python asr_cli.py transcribe\n（目录：{config.TRANSCRIPT_DIR}）")
        return
    if limit is not None:
        transcripts = transcripts[:limit]

    print(f"待提取 {len(transcripts)} 个转写文件\n")
    for idx, path in enumerate(transcripts, 1):
        stem = os.path.splitext(os.path.basename(path))[0]
        print(f"===== [{idx}/{len(transcripts)}] {stem} =====")
        try:
            extract_one(path, force=force)
        except llm.LLMError as exc:
            print(f"[中断] {exc}")
            return
        except Exception as exc:  # noqa: BLE001
            print(f"[失败] {stem}：{exc}\n")


def build_summary() -> None:
    """跨视频汇总一份「答辩高频问题清单」。"""
    files = _all_qa_files()
    if not files:
        print("还没有任何问答结果，先运行：python asr_cli.py qa")
        return

    flat: list[str] = []
    per_video: dict[str, list[dict]] = {}
    for path in files:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        stem = data.get("stem") or os.path.splitext(os.path.basename(path))[0]
        per_video[stem] = data.get("items") or []
        for item in per_video[stem]:
            flat.append(f"[{stem}] {item.get('category', '其他')} | {item.get('question', '')}")

    if not flat:
        print("问答结果为空，无需汇总。")
        return

    os.makedirs(config.QA_DIR, exist_ok=True)
    all_path = os.path.join(config.QA_DIR, "_all_questions.json")
    with open(all_path, "w", encoding="utf-8") as f:
        json.dump(
            {"n_videos": len(per_video), "n_questions": len(flat), "items": flat},
            f, ensure_ascii=False, indent=2,
        )
    print(f"[汇总] 共 {len(per_video)} 个视频 / {len(flat)} 条问题，已写入 {all_path}")

    user = prompts.SUMMARY_USER_TEMPLATE.format(
        n_videos=len(per_video), n_questions=len(flat), content="\n".join(flat),
    )
    print("[汇总] 调用大模型归纳高频问题 ...")
    md = llm.chat([
        {"role": "system", "content": prompts.SUMMARY_SYSTEM},
        {"role": "user", "content": user},
    ])

    out_md = os.path.join(config.QA_DIR, "_高频答辩问题清单.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md.strip() + "\n")
    print(f"[汇总] 完成：{out_md}")

