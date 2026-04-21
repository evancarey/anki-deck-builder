import argparse

from .app import run_app
from .config import AppConfig
from .core.deck_types import DECK_TYPE_PLUGINS
from .core.schemas import SCHEMA_PLUGINS


DEFAULT_DECK_PREFIX = "French"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Anki decks with plugin-based schemas and deck types"
    )
    parser.add_argument("--input", default="french_sentences.csv")
    parser.add_argument("--output", default="french_sentences.apkg")
    parser.add_argument("--voice", default="Lea")
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--deck-prefix", default=DEFAULT_DECK_PREFIX)
    parser.add_argument("--schema", choices=sorted(SCHEMA_PLUGINS.keys()), default="french-sentences")
    parser.add_argument("--deck-type", choices=sorted(DECK_TYPE_PLUGINS.keys()), default="french-ipa-audio")
    parser.add_argument("--freq-mode", choices=["avg", "min"], default="avg")
    parser.add_argument(
        "--level-mode",
        choices=["respect-existing", "recompute-all", "report-only"],
        default="respect-existing",
    )
    parser.add_argument("--export-level-report", default="")
    parser.add_argument("--write-updated-csv", default="")
    parser.add_argument("--in-place", action="store_true")
    parser.add_argument("--backup", action="store_true")
    parser.add_argument("--diff-output", default="")
    parser.add_argument("--export-anki-csv", default="")
    parser.add_argument("--export-media-dir", default="")
    parser.add_argument("--skip-apkg", action="store_true")
    parser.add_argument("--cache-manifest", default="")
    parser.add_argument("--no-cache-cleanup", action="store_true")
    parser.add_argument("--cache-dir", default=".cache")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> AppConfig:
    return AppConfig(
        input=args.input,
        output=args.output,
        voice=args.voice,
        workers=args.workers,
        deck_prefix=args.deck_prefix,
        schema=args.schema,
        deck_type=args.deck_type,
        freq_mode=args.freq_mode,
        level_mode=args.level_mode,
        export_level_report=args.export_level_report,
        write_updated_csv=args.write_updated_csv,
        in_place=args.in_place,
        backup=args.backup,
        diff_output=args.diff_output,
        export_anki_csv=args.export_anki_csv,
        export_media_dir=args.export_media_dir,
        skip_apkg=args.skip_apkg,
        cache_manifest=args.cache_manifest,
        no_cache_cleanup=args.no_cache_cleanup,
        cache_dir=args.cache_dir,
    )


def main() -> None:
    args = parse_args()
    config = build_config(args)
    run_app(config)
