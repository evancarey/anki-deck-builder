import csv
import os

from anki_deck_builder.domain.models import AudioBundle, StudyItem
from anki_deck_builder.io.media import copy_file_if_exists, ensure_dir


def export_anki_import_csv(items: list[StudyItem], output_path: str, audio_lookup: dict[str, AudioBundle]):
    fieldnames = ["Prompt", "IPA", "Answer", "Image", "AudioSlow", "AudioNormal", "Tags"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for item in items:
            audio = audio_lookup[item.prompt]
            image_html = f'<img src="{os.path.basename(item.image)}">' if item.image else ""

            writer.writerow(
                {
                    "Prompt": item.prompt,
                    "IPA": item.ipa,
                    "Answer": item.answer,
                    "Image": image_html,
                    "AudioSlow": f"[sound:{os.path.basename(audio.slow)}]" if audio.slow else "",
                    "AudioNormal": f"[sound:{os.path.basename(audio.normal)}]" if audio.normal else "",
                    "Tags": " ".join(item.tags),
                }
            )
    print(f"\n📝 Exported Anki-import CSV: {output_path}")


def export_media_bundle(items: list[StudyItem], media_dir: str, audio_lookup: dict[str, AudioBundle]):
    ensure_dir(media_dir)
    copied = 0
    missing = []
    seen = set()

    for item in items:
        audio = audio_lookup[item.prompt]
        for media_path in [audio.slow, audio.normal]:
            if not media_path:
                continue
            media_key = os.path.basename(media_path)
            if media_key in seen:
                continue
            seen.add(media_key)
            if os.path.exists(media_path):
                copy_file_if_exists(media_path, media_dir)
                copied += 1
            else:
                missing.append(media_path)

        if item.image:
            image_basename = os.path.basename(item.image)
            if image_basename not in seen:
                seen.add(image_basename)
                if os.path.exists(item.image):
                    copy_file_if_exists(item.image, media_dir)
                    copied += 1
                else:
                    missing.append(item.image)

    print(f"\n📦 Copied {copied} media files to: {media_dir}")
    if missing:
        print(f"⚠️ Missing media files: {len(missing)}")
        for path in missing[:20]:
            print(f"  - {path}")
        if len(missing) > 20:
            print("  - ...")
