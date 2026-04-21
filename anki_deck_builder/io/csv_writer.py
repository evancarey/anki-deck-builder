import csv
import shutil
from datetime import datetime

from anki_deck_builder.domain.models import StudyItem


def make_backup(path: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{path}.{timestamp}.bak"
    shutil.copy2(path, backup_path)
    print(f"\n🗂 Created backup: {backup_path}")
    return backup_path


def write_updated_csv(items: list[StudyItem], output_path: str):
    fieldnames = ["French", "IPA", "English", "Level", "Tags", "Image"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "French": item.prompt,
                    "IPA": item.ipa,
                    "English": item.answer,
                    "Level": item.level,
                    "Tags": ",".join(item.tags),
                    "Image": item.image,
                }
            )
    print(f"\n💾 Wrote updated CSV: {output_path}")


def maybe_write_updated_csv(
    items: list[StudyItem],
    input_csv: str,
    write_updated_csv_path: str,
    in_place: bool,
    backup: bool,
):
    if in_place and write_updated_csv_path:
        raise ValueError("Use either --in-place or --write-updated-csv, not both.")

    if not in_place and not write_updated_csv_path:
        return

    target_path = input_csv if in_place else write_updated_csv_path
    if in_place and backup:
        make_backup(input_csv)
    write_updated_csv(items, target_path)


def export_diff_csv(items: list[StudyItem], output_path: str):
    fieldnames = [
        "Prompt",
        "Answer",
        "RawLevel",
        "FinalLevel",
        "LevelChanged",
        "OriginalTags",
        "FinalTags",
        "TagsChanged",
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
                    "RawLevel": item.raw_level,
                    "FinalLevel": item.level,
                    "LevelChanged": "yes" if item.raw_level != item.level else "no",
                    "OriginalTags": ",".join(item.original_tags),
                    "FinalTags": ",".join(item.tags),
                    "TagsChanged": "yes" if item.original_tags != item.tags else "no",
                    "Image": item.image,
                }
            )
    print(f"\n📝 Wrote diff CSV: {output_path}")
