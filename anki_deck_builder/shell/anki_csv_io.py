from __future__ import annotations

import csv
import os

from ..core.models import PreparedItem


def export_anki_import_csv(items: list[PreparedItem], audio_by_prompt: dict[str, dict[str, str]], output_path: str) -> None:
    fieldnames = ["French", "IPA", "English", "Image", "AudioSlow", "AudioNormal", "Tags"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            audio = audio_by_prompt[item.prompt]
            image_html = f'<img src="{os.path.basename(item.image)}">' if item.image else ""
            writer.writerow(
                {
                    "French": item.prompt,
                    "IPA": item.ipa,
                    "English": item.answer,
                    "Image": image_html,
                    "AudioSlow": f"[sound:{os.path.basename(audio['slow_path'])}]",
                    "AudioNormal": f"[sound:{os.path.basename(audio['normal_path'])}]",
                    "Tags": " ".join(item.tags),
                }
            )
    print(f"\n📝 Exported Anki-import CSV: {output_path}")
