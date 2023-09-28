import argparse
import fileinput
import json
from collections import defaultdict
from pathlib import Path


def get_parser():
    parser = argparse.ArgumentParser(
        description="Process Raw data to Kaldi-like format"
    )
    parser.add_argument(
        "--source_dir",
        type=Path,
        default=Path("downloads"),
    )
    parser.add_argument(
        "--target_dir",
        type=Path,
        default=Path("data"),
    )
    parser.add_argument(
        "--langs",
        type=str,  # comma separated values
    )
    parser.add_argument(
        "--tasks",
        type=str,  # comma separated values
    )
    return parser


def build_dir(task, lang, split):
    target_dir = args.target_dir / f"w2g_{task}_{lang}_{split}"
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def _cleaner(s):
    return "".join([chr(ord(c)) for c in s if ord(c) != 160])


def write_dir(target_dir, metadata):
    wavscp = open(target_dir / "wav.scp", "w", encoding="utf-8")
    text = open(target_dir / "text", "w", encoding="utf-8")
    utt2spk = open(target_dir / "utt2spk", "w", encoding="utf-8")
    spk2utt = open(target_dir / "spk2utt", "w", encoding="utf-8")
    lm = open(target_dir / "lm.txt", "w", encoding="utf-8")

    count = 0
    spk2utt.write("dummy")
    for fname, meta in metadata.items():
        if len(meta[task]) < 1:
            continue
        if " " in fname:
            continue

        _id = f"dummy_{lang}_{task}_{meta['id']}"
        _id = "".join(_id.split())

        content = f"<lang|{lang}> <task|{task}> {meta[task]}"
        content = _cleaner(content)

        wavscp.write(f"{_id} downloads/data/{lang}/audio/{split}/{fname}\n")
        text.write(f"{_id} {content}\n")
        utt2spk.write(f"{_id} dummy\n")
        spk2utt.write(f" {_id}")
        lm.write(f"{count:010} {content}\n")

        count += 1

    wavscp.close()
    text.close()
    utt2spk.close()
    spk2utt.close()

    print(f"{target_dir}: {count} lines written.")


def merge_dir(target_dir, source_dirs):
    for fname in ("wav.scp", "text", "utt2spk", "spk2utt", "lm.txt"):
        target = open(target_dir / fname, "w", encoding="utf-8")
        count = 0
        for d in source_dirs:
            with open(d / fname, encoding="utf-8") as f:
                for line in f:
                    if fname == "lm.txt":
                        target.write(f"{count:010}{line[10:]}")
                    else:
                        target.write(line)
                    count += 1
    print(f"{target_dir}: merged {source_dirs}")


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()

    args.langs = args.langs.split(",")
    args.tasks = args.tasks.split(",")

    args.target_dir.mkdir(parents=True, exist_ok=True)
    with open(
        args.target_dir / "non_linguistic_symbols.txt", "w", encoding="utf-8"
    ) as f:
        for lang in args.langs:
            f.write(f"<lang|{lang}>\n")
        for task in args.tasks:
            f.write(f"<task|{task}>\n")

    for lang in args.langs:
        for split in ("train", "dev", "test"):
            metadata = json.load(
                open(
                    args.source_dir / "data" / lang / f"{split}.json", encoding="utf-8"
                )
            )
            for task in args.tasks:
                target_dir = build_dir(task, lang, split)
                write_dir(target_dir, metadata)

    for split in ("train", "dev"):
        for lang in args.langs:
            target_dir = build_dir("all", lang, split)
            merge_dir(
                target_dir,
                [args.target_dir / f"w2g_{task}_{lang}_{split}" for task in args.tasks],
            )
        for task in args.tasks:
            target_dir = build_dir(task, "full", split)
            merge_dir(
                target_dir,
                [args.target_dir / f"w2g_{task}_{lang}_{split}" for lang in args.langs],
            )
        target_dir = build_dir("all", "full", split)
        merge_dir(
            target_dir,
            [
                args.target_dir / f"w2g_{task}_{lang}_{split}"
                for lang in args.langs
                for task in args.tasks
            ],
        )

    print("pre-processing finished.")