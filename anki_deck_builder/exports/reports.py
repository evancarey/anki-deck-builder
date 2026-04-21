import csv

from anki_deck_builder.domain.models import StudyItem


def print_level_report(items: list[StudyItem]):
    total = len(items)
    manual = sum(1 for i in items if i.level_source == "manual")
    auto = sum(1 for i in items if i.level_source == "auto")
    differing = sum(1 for i in items if i.raw_level and i.raw_level != i.inferred_level)

    print("\n📊 Level report")
    print(f"  - Total rows: {total}")
    print(f"  - Manual levels kept: {manual}")
    print(f"  - Auto-filled levels: {auto}")
    print(f"  - Manual levels differing from inference: {differing}")

    if differing:
        print("\nExamples where manual level differs from inferred level:")
        shown = 0
        for item in items:
            if item.raw_level and item.raw_level != item.inferred_level:
                print(f"  - [{item.raw_level} vs inferred {item.inferred_level}] {item.prompt}")
                shown += 1
                if shown >= 10:
                    break


def export_level_report_csv(items: list[StudyItem], output_path: str):
    fieldnames = [
        "Prompt",
        "Answer",
        "IPA",
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
                    "Prompt": item.prompt,
                    "Answer": item.answer,
                    "IPA": item.ipa,
                    "RawLevel": item.raw_level,
                    "InferredLevel": item.inferred_level,
                    "FinalLevel": item.level,
                    "LevelSource": item.level_source,
                    "avg_zipf": f"{item.extra.get('avg_zipf', 0):.3f}",
                    "min_zipf": f"{item.extra.get('min_zipf', 0):.3f}",
                    "max_zipf": f"{item.extra.get('max_zipf', 0):.3f}",
                    "token_count": item.extra.get("token_count", 0),
                    "tokens": item.extra.get("tokens", ""),
                    "Tags": ",".join(item.tags),
                    "Image": item.image,
                }
            )
    print(f"\n📝 Exported level review CSV: {output_path}")
