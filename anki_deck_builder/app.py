from anki_deck_builder.audio.cache import default_manifest_name
from anki_deck_builder.audio.polly import PollySynthesizer
from anki_deck_builder.audio.service import AudioService
from anki_deck_builder.config import AppConfig
from anki_deck_builder.deck_types import get_deck_type
from anki_deck_builder.exports.anki_csv import export_anki_import_csv, export_media_bundle
from anki_deck_builder.exports.apkg import write_apkg
from anki_deck_builder.exports.reports import export_level_report_csv, print_level_report
from anki_deck_builder.io.csv_reader import load_rows
from anki_deck_builder.io.csv_writer import export_diff_csv, maybe_write_updated_csv
from anki_deck_builder.io.manifest import (
    build_manifest_payload,
    cleanup_audio_cache_from_manifests,
    write_manifest,
)
from anki_deck_builder.processing.prepare import prepare_item
from anki_deck_builder.schemas import get_schema
from anki_deck_builder.domain.models import SourceRow


class DeckBuilderApp:
    def __init__(self, config: AppConfig, schema, deck_type, audio_service: AudioService):
        self.config = config
        self.schema = schema
        self.deck_type = deck_type
        self.audio_service = audio_service

    def run(self):
        raw_rows = load_rows(self.config.input_csv)
        if not raw_rows:
            raise ValueError("Input CSV has no rows")

        headers = list(raw_rows[0].keys())
        self.schema.validate_headers(headers)

        items = [
            self.schema.to_study_item(SourceRow(row))
            for row in raw_rows
        ]
        items = [
            prepare_item(item, self.config.freq_mode, self.config.level_mode)
            for item in items
        ]

        if self.config.level_mode == "report-only":
            print_level_report(items)

        if self.config.export_level_report:
            export_level_report_csv(items, self.config.export_level_report)

        maybe_write_updated_csv(
            items=items,
            input_csv=self.config.input_csv,
            write_updated_csv_path=self.config.write_updated_csv_path,
            in_place=self.config.in_place,
            backup=self.config.backup,
        )

        if self.config.diff_output:
            export_diff_csv(items, self.config.diff_output)

        print(f"\n🔊 Processing audio with {self.config.workers} workers...\n")
        audio_lookup, total_chars, rows_regenerated = self.audio_service.ensure_audio_for_items(
            items=items,
            voice_id=self.config.voice_id,
            required_modes=self.deck_type.required_audio_modes(),
        )

        cost_usd = total_chars * 16 / 1_000_000
        print(f"\n💰 Estimated AWS Polly cost for this run: ${cost_usd:.4f} USD")
        print(f"🔁 Rows with regenerated audio: {rows_regenerated}")

        if self.config.export_anki_csv_path:
            export_anki_import_csv(items, self.config.export_anki_csv_path, audio_lookup)

        if self.config.export_media_dir:
            export_media_bundle(items, self.config.export_media_dir, audio_lookup)

        manifest_name = self.config.cache_manifest or default_manifest_name(
            self.config.input_csv,
            self.config.deck_prefix,
            self.config.voice_id,
        )
        manifest_payload = build_manifest_payload(
            items=items,
            input_csv=self.config.input_csv,
            output_file=self.config.output_file,
            deck_prefix=self.config.deck_prefix,
            voice_id=self.config.voice_id,
            audio_lookup=audio_lookup,
        )
        manifest_file = write_manifest(manifest_name, manifest_payload)
        print(f"\n🗂 Wrote cache manifest: {manifest_file}")

        if not self.config.no_cache_cleanup:
            cleanup_audio_cache_from_manifests()
        else:
            print("\n⏭ Skipped cache cleanup (--no-cache-cleanup)")

        if self.config.skip_apkg:
            print("\n⏭ Skipped .apkg generation (--skip-apkg)")
            return

        print("\n📦 Building decks...\n")
        write_apkg(
            items=items,
            deck_type=self.deck_type,
            output_file=self.config.output_file,
            audio_lookup=audio_lookup,
            deck_prefix=self.config.deck_prefix,
        )


def build_application(config: AppConfig) -> DeckBuilderApp:
    schema = get_schema(config.schema_name)
    deck_type = get_deck_type(config.deck_type_name)
    audio_service = AudioService(
        synthesizer=PollySynthesizer(),
        workers=config.workers,
    )
    return DeckBuilderApp(
        config=config,
        schema=schema,
        deck_type=deck_type,
        audio_service=audio_service,
    )
