from __future__ import annotations

import csv

from ..core.models import PreparedItem


def print_level_report(items: list[PreparedItem]) -> None:
    total = len(items)
    manual = sum(1 for item in items if item.level_source == "manual")
    auto = sum(1 for item in items if item.level_source == "auto")
    differing = sum(1 for item in items if item.raw_level and item.raw_level != item.inferred_level)

    print("\n📊 Level report")
    print(f"  - Total rows: {total}")
    print(f"  - Manual levels kept: {manual}")
    print(f"  - Auto-filled levels: {auto}")
    print(f"  - Manual levels differing from inference: {differing}")


def export_level_report_csv(items: list[PreparedItem], output_path: str) -> None:
    fieldnames = [
        "French",
        "IPA",
        "English",
        "RawLevel",
        "InferredLevel",
        "FinalLevel",
        "LevelSource",
        "avg_zipf",
        "min_zipf",
        "max_zipf",
        "token_count",
        "tokens",
        "Tags",
        "Image",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "French": item.prompt,
                    "IPA": item.ipa,
                    "English": item.answer,
                    "RawLevel": item.raw_level,
                    "InferredLevel": item.inferred_level,
                    "FinalLevel": item.level,
                    "LevelSource": item.level_source,
                    "avg_zipf": f"{item.extra['avg_zipf']:.3f}",
                    "min_zipf": f"{item.extra['min_zipf']:.3f}",
                    "max_zipf": f"{item.extra['max_zipf']:.3f}",
                    "token_count": item.extra["token_count"],
                    "tokens": " ".join(item.extra["tokens"]),
                    "Tags": ",".join(item.tags),
                    "Image": item.image,
                }
            )
    print(f"\n📝 Exported level review CSV: {output_path}")
