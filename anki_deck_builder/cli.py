import argparse

from .app import build_application
from .config import AppConfig, DEFAULT_DECK_PREFIX
from .deck_types import available_deck_types
from .schemas import available_schemas


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate Anki decks with pluggable schemas and deck types"
    )
    parser.add_argument("--input", default="french_sentences.csv")
    parser.add_argument("--output", default="french_sentences.apkg")
    parser.add_argument("--voice", default="Lea")
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--deck-prefix", default=DEFAULT_DECK_PREFIX)

    parser.add_argument(
        "--schema",
        choices=sorted(available_schemas().keys()),
        default="french-sentences",
        help="Input schema plugin to use",
    )
    parser.add_argument(
        "--deck-type",
        choices=sorted(available_deck_types().keys()),
        default="french-ipa-audio",
        help="Deck type plugin to use",
    )

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
        help="Optional output CSV path formatted for Anki note import",
    )
    parser.add_argument(
        "--export-media-dir",
        default="",
        help="Optional directory to copy audio and image media into for Anki CSV import",
    )
    parser.add_argument(
        "--skip-apkg",
        action="store_true",
        help="Skip writing the .apkg package and only write CSV/report/media outputs",
    )
    parser.add_argument(
        "--cache-manifest",
        default="",
        help="Optional manifest name used for shared-cache cleanup",
    )
    parser.add_argument(
        "--no-cache-cleanup",
        action="store_true",
        help="Do not delete orphaned shared-cache audio files after writing the current manifest.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    config = AppConfig(
        input_csv=args.input,
        output_file=args.output,
        voice_id=args.voice,
        workers=args.workers,
        deck_prefix=args.deck_prefix,
        schema_name=args.schema,
        deck_type_name=args.deck_type,
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
        cache_manifest=args.cache_manifest,
        no_cache_cleanup=args.no_cache_cleanup,
    )
    app = build_application(config)
    app.run()
