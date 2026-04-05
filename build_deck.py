import argparse
import csv
import hashlib
import json
import os
import re
import shutil
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
import genanki
from tqdm import tqdm
from wordfreq import zipf_frequency


CACHE_FILE = ".audio_cache.json"
DEFAULT_DECK_PREFIX = "French"
MODEL_ID = 1091735999


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate Anki decks with French audio, level inference, and frequency-based ordering"
    )
    parser.add_argument("--input", default="french_sentences.csv")
    parser.add_argument("--output", default="french_sentences.apkg")
    parser.add_argument("--voice", default="Lea")
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--deck-prefix", default=DEFAULT_DECK_PREFIX)
    parser.add_argument(
        "--freq-mode",
        choices=["avg", "min"],
        default="avg",
        help="How to score sentence frequency: avg=average word frequency, min=rarest word",
    )
    parser.add_argument(
        "--level-mode",
        choices=["respect-existing", "recompute-all", "report-only"],
        default="respect-existing",
        help=(
            "How to handle Level values: "
            "respect-existing = keep non-empty values and infer blanks; "
            "recompute-all = ignore CSV levels and infer all; "
            "report-only = same as respect-existing, plus print comparison report"
        ),
    )
    parser.add_argument(
        "--export-level-report",
        default="",
        help="Optional output CSV path for reviewing level inference results",
    )
    parser.add_argument(
        "--write-updated-csv",
        default="",
        help="Optional output CSV path with updated levels and tags",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Write updated CSV back to the input file",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="When used with --in-place, create a timestamped backup first",
    )
    parser.add_argument(
        "--diff-output",
        default="",
        help="Optional output CSV path describing row-level changes",
    )
    parser.add_argument(
        "--export-anki-csv",
        default="",
        help=(
            "Optional output CSV path formatted for Anki note import. "
            "Columns: French,IPA,English,Image,AudioSlow,AudioNormal,Tags"
        ),
    )
    parser.add_argument(
        "--export-media-dir",
        default="",
        help=(
            "Optional directory to copy audio and image media into for Anki CSV import "
            "(for example a temp folder you will drag into Anki)."
        ),
    )
    parser.add_argument(
        "--skip-apkg",
        action="store_true",
        help="Skip writing the .apkg package and only write CSV/report/media outputs",
    )
    return parser.parse_args()


def create_model():
    return genanki.Model(
        MODEL_ID,
        "French IPA Audio Model",
        fields=[
            {"name": "French"},
            {"name": "IPA"},
            {"name": "English"},
            {"name": "Image"},
            {"name": "AudioSlow"},
            {"name": "AudioNormal"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": """
                    <div style="font-size:28px;">{{French}}</div>
                    <div style="font-size:18px; color:gray;"><i>{{IPA}}</i></div>
                    {{Image}}
                    <br>
                    {{AudioSlow}}<br>
                    {{AudioNormal}}
                """,
                "afmt": """
                    {{FrontSide}}
                    <hr id="answer">
                    <div style="font-size:24px;">{{English}}</div>
                """,
            },
        ],
    )


def make_guid(fr, en):
    return hashlib.md5((fr + en).encode("utf-8")).hexdigest()


def make_content_hash(fr, ipa, en):
    return hashlib.md5((fr + ipa + en).encode("utf-8")).hexdigest()


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def load_rows(csv_file):
    with open(csv_file, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def escape_ssml_text(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def synthesize(polly, text, filename, voice_id, slow=False):
    try:
        if slow:
            ssml = f"<speak><prosody rate='70%'>{escape_ssml_text(text)}</prosody></speak>"
            response = polly.synthesize_speech(
                Text=ssml,
                TextType="ssml",
                OutputFormat="mp3",
                VoiceId=voice_id,
            )
        else:
            response = polly.synthesize_speech(
                Text=text,
                OutputFormat="mp3",
                VoiceId=voice_id,
            )

        with open(filename, "wb") as f:
            f.write(response["AudioStream"].read())

        return filename
    except Exception as e:
        print(f"\n❌ Error generating {filename}: {e}")
        return None


def tokenize_french(text):
    text = text.lower()
    tokens = re.findall(r"[a-zàâçéèêëîïôûùüÿñæœ'-]+", text, flags=re.IGNORECASE)
    normalized = []
    for token in tokens:
        token = token.strip("-'")
        if not token:
            continue
        parts = re.split(r"[']", token)
        for part in parts:
            part = part.strip("- ")
            if part:
                normalized.append(part)
    return normalized


def word_zipf(token):
    return zipf_frequency(token, "fr")


def sentence_frequency_stats(text):
    tokens = tokenize_french(text)
    if not tokens:
        return {
            "tokens": [],
            "token_count": 0,
            "avg_zipf": 0.0,
            "min_zipf": 0.0,
            "max_zipf": 0.0,
        }

    freqs = [word_zipf(token) for token in tokens]
    return {
        "tokens": tokens,
        "token_count": len(tokens),
        "avg_zipf": sum(freqs) / len(freqs),
        "min_zipf": min(freqs),
        "max_zipf": max(freqs),
    }


def frequency_bucket(avg_zipf, min_zipf):
    if avg_zipf >= 5.2 and min_zipf >= 3.5:
        return "freq_common"
    if avg_zipf >= 4.2 and min_zipf >= 2.5:
        return "freq_mid"
    return "freq_rare"


def frequency_rank_tag(avg_zipf):
    bucket = int(max(0, min(8, round(avg_zipf))))
    return f"freq_zipf_{bucket}"


def deterministic_deck_id(name):
    digest = hashlib.md5(name.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def infer_level(avg_zipf, min_zipf, token_count):
    if avg_zipf >= 5.2 and min_zipf >= 3.2 and token_count <= 8:
        return "A1"
    if avg_zipf >= 4.7 and min_zipf >= 2.5 and token_count <= 12:
        return "A2"
    if avg_zipf >= 4.0 and min_zipf >= 1.8 and token_count <= 18:
        return "B1"
    return "B2"


def resolve_level(raw_level, inferred_level, level_mode):
    raw_level = (raw_level or "").strip()

    if level_mode == "recompute-all":
        return inferred_level, "auto"

    if level_mode in {"respect-existing", "report-only"}:
        if raw_level:
            return raw_level, "manual"
        return inferred_level, "auto"

    raise ValueError(f"Unsupported level_mode: {level_mode}")


def prepare_rows(rows, freq_mode, level_mode):
    prepared = []

    for row in rows:
        fr = row["French"]
        ipa = row["IPA"]
        en = row["English"]

        stats = sentence_frequency_stats(fr)
        avg_zipf = stats["avg_zipf"]
        min_zipf = stats["min_zipf"]
        token_count = stats["token_count"]

        raw_level = (row.get("Level") or "").strip()
        inferred_level = infer_level(avg_zipf, min_zipf, token_count)
        level, level_source = resolve_level(raw_level, inferred_level, level_mode)

        freq_score = avg_zipf if freq_mode == "avg" else min_zipf

        base_tags = []
        raw_tags = row.get("Tags", "")
        if raw_tags:
            base_tags = [t.strip() for t in raw_tags.split(",") if t.strip()]

        original_tags = list(base_tags)

        auto_tags = [
            frequency_bucket(avg_zipf, min_zipf),
            frequency_rank_tag(avg_zipf),
            f"level_{level.lower()}",
            f"level_source_{level_source}",
        ]

        if level_source == "auto":
            auto_tags.append(f"level_auto_{inferred_level.lower()}")
        else:
            auto_tags.append("level_manual")

        if raw_level and raw_level != inferred_level:
            auto_tags.append("level_differs_from_inference")
            auto_tags.append(f"level_inferred_{inferred_level.lower()}")

        prepared.append(
            {
                "French": fr,
                "IPA": ipa,
                "English": en,
                "Level": level,
                "RawLevel": raw_level,
                "InferredLevel": inferred_level,
                "LevelSource": level_source,
                "OriginalTags": original_tags,
                "Tags": base_tags + auto_tags,
                "Image": (row.get("Image") or "").strip(),
                "avg_zipf": avg_zipf,
                "min_zipf": min_zipf,
                "max_zipf": stats["max_zipf"],
                "token_count": token_count,
                "tokens": " ".join(stats["tokens"]),
                "freq_score": freq_score,
            }
        )

    return prepared


def print_level_report(rows):
    total = len(rows)
    manual = sum(1 for r in rows if r["LevelSource"] == "manual")
    auto = sum(1 for r in rows if r["LevelSource"] == "auto")
    differing = sum(
        1 for r in rows
        if r["RawLevel"] and r["RawLevel"] != r["InferredLevel"]
    )

    print("\n📊 Level report")
    print(f"  - Total rows: {total}")
    print(f"  - Manual levels kept: {manual}")
    print(f"  - Auto-filled levels: {auto}")
    print(f"  - Manual levels differing from inference: {differing}")

    if differing:
        print("\nExamples where manual level differs from inferred level:")
        shown = 0
        for row in rows:
            if row["RawLevel"] and row["RawLevel"] != row["InferredLevel"]:
                print(
                    f"  - [{row['RawLevel']} vs inferred {row['InferredLevel']}] "
                    f"{row['French']}"
                )
                shown += 1
                if shown >= 10:
                    break


def export_level_report_csv(rows, output_path):
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

        for row in rows:
            writer.writerow(
                {
                    "French": row["French"],
                    "IPA": row["IPA"],
                    "English": row["English"],
                    "RawLevel": row["RawLevel"],
                    "InferredLevel": row["InferredLevel"],
                    "FinalLevel": row["Level"],
                    "LevelSource": row["LevelSource"],
                    "avg_zipf": f"{row['avg_zipf']:.3f}",
                    "min_zipf": f"{row['min_zipf']:.3f}",
                    "max_zipf": f"{row['max_zipf']:.3f}",
                    "token_count": row["token_count"],
                    "tokens": row["tokens"],
                    "Tags": ",".join(row["Tags"]),
                    "Image": row["Image"],
                }
            )

    print(f"\n📝 Exported level review CSV: {output_path}")


def make_backup(path):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{path}.{timestamp}.bak"
    shutil.copy2(path, backup_path)
    print(f"\n🗂 Created backup: {backup_path}")
    return backup_path


def write_updated_csv(rows, output_path):
    fieldnames = ["French", "IPA", "English", "Level", "Tags", "Image"]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    "French": row["French"],
                    "IPA": row["IPA"],
                    "English": row["English"],
                    "Level": row["Level"],
                    "Tags": ",".join(row["Tags"]),
                    "Image": row["Image"],
                }
            )

    print(f"\n💾 Wrote updated CSV: {output_path}")


def export_diff_csv(rows, output_path):
    fieldnames = [
        "French",
        "IPA",
        "English",
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

        for row in rows:
            original_tags = row.get("OriginalTags", [])
            final_tags = row["Tags"]

            writer.writerow(
                {
                    "French": row["French"],
                    "IPA": row["IPA"],
                    "English": row["English"],
                    "RawLevel": row["RawLevel"],
                    "FinalLevel": row["Level"],
                    "LevelChanged": "yes" if row["RawLevel"] != row["Level"] else "no",
                    "OriginalTags": ",".join(original_tags),
                    "FinalTags": ",".join(final_tags),
                    "TagsChanged": "yes" if original_tags != final_tags else "no",
                    "Image": row["Image"],
                }
            )

    print(f"\n📝 Wrote diff CSV: {output_path}")


def maybe_write_updated_csv(rows, input_csv, write_updated_csv_path, in_place, backup):
    if in_place and write_updated_csv_path:
        raise ValueError("Use either --in-place or --write-updated-csv, not both.")

    if not in_place and not write_updated_csv_path:
        return

    target_path = input_csv if in_place else write_updated_csv_path

    if in_place and backup:
        make_backup(input_csv)

    write_updated_csv(rows, target_path)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def copy_file_if_exists(src, dst_dir):
    if not src or not os.path.exists(src):
        return None
    ensure_dir(dst_dir)
    filename = os.path.basename(src)
    dst = os.path.join(dst_dir, filename)
    shutil.copy2(src, dst)
    return dst


def export_anki_import_csv(rows, output_path):
    fieldnames = [
        "French",
        "IPA",
        "English",
        "Image",
        "AudioSlow",
        "AudioNormal",
        "Tags",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            guid = make_guid(row["French"], row["English"])
            slow_file = f"{guid}_slow.mp3"
            normal_file = f"{guid}_normal.mp3"

            image_html = ""
            image_name = row["Image"]
            if image_name:
                image_html = f'<img src="{os.path.basename(image_name)}">'

            writer.writerow(
                {
                    "French": row["French"],
                    "IPA": row["IPA"],
                    "English": row["English"],
                    "Image": image_html,
                    "AudioSlow": f"[sound:{slow_file}]",
                    "AudioNormal": f"[sound:{normal_file}]",
                    "Tags": " ".join(row["Tags"]),
                }
            )

    print(f"\n📝 Exported Anki-import CSV: {output_path}")


def export_media_bundle(rows, media_dir):
    ensure_dir(media_dir)
    copied = 0
    missing = []

    seen = set()

    for row in rows:
        guid = make_guid(row["French"], row["English"])
        slow_file = f"{guid}_slow.mp3"
        normal_file = f"{guid}_normal.mp3"

        for media_path in [slow_file, normal_file]:
            if media_path in seen:
                continue
            seen.add(media_path)
            if os.path.exists(media_path):
                copy_file_if_exists(media_path, media_dir)
                copied += 1
            else:
                missing.append(media_path)

        image_path = row["Image"]
        if image_path:
            image_basename = os.path.basename(image_path)
            if image_basename not in seen:
                seen.add(image_basename)
                if os.path.exists(image_path):
                    copy_file_if_exists(image_path, media_dir)
                    copied += 1
                else:
                    missing.append(image_path)

    print(f"\n📦 Copied {copied} media files to: {media_dir}")
    if missing:
        print(f"⚠️ Missing media files: {len(missing)}")
        for path in missing[:20]:
            print(f"  - {path}")
        if len(missing) > 20:
            print("  - ...")


def maybe_export_csv_media(rows, export_anki_csv_path, export_media_dir):
    if export_anki_csv_path:
        export_anki_import_csv(rows, export_anki_csv_path)

    if export_media_dir:
        export_media_bundle(rows, export_media_dir)


def build_decks(
    csv_file,
    output_file,
    voice_id,
    workers,
    deck_prefix,
    freq_mode,
    level_mode,
    export_level_report,
    write_updated_csv_path,
    in_place,
    backup,
    diff_output,
    export_anki_csv_path,
    export_media_dir,
    skip_apkg,
):
    polly = boto3.client("polly", region_name="us-east-1")
    model = create_model()

    raw_rows = load_rows(csv_file)
    rows = prepare_rows(raw_rows, freq_mode, level_mode)

    if level_mode == "report-only":
        print_level_report(rows)

    if export_level_report:
        export_level_report_csv(rows, export_level_report)

    maybe_write_updated_csv(
        rows=rows,
        input_csv=csv_file,
        write_updated_csv_path=write_updated_csv_path,
        in_place=in_place,
        backup=backup,
    )

    if diff_output:
        export_diff_csv(rows, diff_output)

    cache = load_cache()
    media_files = set()
    futures = []
    total_chars = 0
    rows_regenerated = 0

    print(f"\n🔊 Processing audio with {workers} workers...\n")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        for row in rows:
            fr = row["French"]
            ipa = row["IPA"]
            en = row["English"]

            guid = make_guid(fr, en)
            content_hash = make_content_hash(fr, ipa, en)

            slow_file = f"{guid}_slow.mp3"
            normal_file = f"{guid}_normal.mp3"

            if (
                cache.get(guid) == content_hash
                and os.path.exists(slow_file)
                and os.path.exists(normal_file)
            ):
                media_files.add(slow_file)
                media_files.add(normal_file)
                continue

            cache[guid] = content_hash
            rows_regenerated += 1
            total_chars += len(fr) * 2

            futures.append(
                executor.submit(synthesize, polly, fr, slow_file, voice_id, True)
            )
            futures.append(
                executor.submit(synthesize, polly, fr, normal_file, voice_id, False)
            )

        for future in tqdm(as_completed(futures), total=len(futures), desc="Audio"):
            result = future.result()
            if result:
                media_files.add(result)

    save_cache(cache)

    cost_usd = total_chars * 16 / 1_000_000
    print(f"\n💰 Estimated AWS Polly cost for this run: ${cost_usd:.4f} USD")
    print(f"🔁 Rows with regenerated audio: {rows_regenerated}")

    maybe_export_csv_media(
        rows=rows,
        export_anki_csv_path=export_anki_csv_path,
        export_media_dir=export_media_dir,
    )

    if skip_apkg:
        print("\n⏭ Skipped .apkg generation (--skip-apkg)")
        return

    print("\n📦 Building decks...\n")

    rows_by_level = {}
    for row in rows:
        rows_by_level.setdefault(row["Level"], []).append(row)

    decks = {}

    for level, level_rows in rows_by_level.items():
        level_rows.sort(key=lambda r: (-r["freq_score"], r["token_count"], r["French"]))

        deck_name = f"{deck_prefix}::{level}"
        deck_id = deterministic_deck_id(deck_name)
        deck = genanki.Deck(deck_id, deck_name)
        decks[level] = deck

        for row in level_rows:
            fr = row["French"]
            ipa = row["IPA"]
            en = row["English"]
            guid = make_guid(fr, en)

            slow_file = f"{guid}_slow.mp3"
            normal_file = f"{guid}_normal.mp3"

            image_html = ""
            image_name = row["Image"]
            if image_name:
                image_html = f'<img src="{os.path.basename(image_name)}">'
                if os.path.exists(image_name):
                    media_files.add(image_name)

            note = genanki.Note(
                model=model,
                fields=[
                    fr,
                    ipa,
                    en,
                    image_html,
                    f"[sound:{slow_file}]",
                    f"[sound:{normal_file}]",
                ],
                tags=row["Tags"],
                guid=guid,
            )

            deck.add_note(note)

    package = genanki.Package(list(decks.values()))
    package.media_files = sorted(media_files)
    package.write_to_file(output_file)

    print(f"\n✅ Decks created: {output_file}")
    print("\nDeck summary:")
    for level in sorted(rows_by_level.keys()):
        print(f"  - {deck_prefix}::{level}: {len(rows_by_level[level])} notes")


def main():
    args = parse_args()
    build_decks(
        csv_file=args.input,
        output_file=args.output,
        voice_id=args.voice,
        workers=args.workers,
        deck_prefix=args.deck_prefix,
        freq_mode=args.freq_mode,
        level_mode=args.level_mode,
        export_level_report=args.export_level_report,
        write_updated_csv_path=args.write_updated_csv,
        in_place=args.in_place,
        backup=args.backup,
        diff_output=args.diff_output,
        export_anki_csv_path=args.export_anki_csv,
        export_media_dir=args.export_media_dir,
        skip_apkg=args.skip_apkg,
    )


if __name__ == "__main__":
    main()
