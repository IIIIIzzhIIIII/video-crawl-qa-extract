"""命令行入口。

参数优先级：命令行 > 上次记忆(data/run_config.json) > config.py 默认值。
也就是说，只要用 -k 指定过一次关键词，之后再运行 `python main.py` 就会沿用它，
不需要每次都重新输入；想换关键词就再带一次 -k，想彻底恢复 config.py 默认值就 --reset。

用法示例：
    python main.py                                   # 沿用上次配置（首次为 config.py 默认）
    python main.py -k "创新创业大赛 国赛 路演 答辩" -m 1
    python main.py -k "互联网+ 国赛 路演" -p 2 -m 3 -q 80
    python main.py --dry-run                         # 只搜索列出候选，不下载
    python main.py --reset                           # 清除记忆，恢复 config.py 默认值
"""
import argparse

import config
from crawler import pipeline, runstate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="B 站创新创业大赛路演视频爬虫")
    parser.add_argument("-k", "--keyword", action="append",
                        help="搜索关键词，可多次指定（覆盖 config.KEYWORDS）")
    parser.add_argument("-p", "--pages", type=int,
                        help="每个关键词抓取页数（默认取 config.PAGES_PER_KEYWORD）")
    parser.add_argument("-m", "--max", type=int,
                        help="最多下载多少个视频，-1 表示不限（默认取 config.MAX_DOWNLOAD）")
    parser.add_argument("-q", "--quality", type=int,
                        help="清晰度 id：80=1080P, 64=720P, 32=480P（默认取 config.QUALITY）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只搜索并列出候选视频，不下载")
    parser.add_argument("--reset", action="store_true",
                        help="清除上次记忆的配置，恢复 config.py 默认值")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.reset:
        print("已清除上次记忆的配置，将恢复 config.py 默认值。"
              if runstate.clear() else "没有需要清除的记忆配置。")
        return

    state = runstate.load()

    # 逐项解析：命令行 > 上次记忆 > config.py 默认值
    if args.keyword:
        config.KEYWORDS = args.keyword
    elif state.get("keywords"):
        config.KEYWORDS = state["keywords"]

    if args.pages is not None:
        config.PAGES_PER_KEYWORD = args.pages
    elif state.get("pages_per_keyword") is not None:
        config.PAGES_PER_KEYWORD = state["pages_per_keyword"]

    if args.max is not None:
        config.MAX_DOWNLOAD = args.max
    elif state.get("max_download") is not None:
        config.MAX_DOWNLOAD = state["max_download"]

    if args.quality is not None:
        config.QUALITY = args.quality
    elif state.get("quality") is not None:
        config.QUALITY = state["quality"]

    # 记忆本次生效的配置，供下次直接复用
    runstate.save({
        "keywords": config.KEYWORDS,
        "pages_per_keyword": config.PAGES_PER_KEYWORD,
        "max_download": config.MAX_DOWNLOAD,
        "quality": config.QUALITY,
    })

    print(f"[配置] 关键词={config.KEYWORDS} 页数={config.PAGES_PER_KEYWORD} "
          f"最多下载={config.MAX_DOWNLOAD} 清晰度={config.QUALITY}")
    if not args.keyword and state.get("keywords"):
        print("[提示] 未指定 -k，沿用上次记忆的关键词；"
              "要更换请加 -k，恢复默认请运行 python main.py --reset")

    pipeline.run(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
