from __future__ import annotations

from .config import AppConfig
from .core.deck_types import DECK_TYPE_PLUGINS, build_note_specs
from .core.planning import build_manifest_payload, default_manifest_name, plan_audio_requests
from .core.prepare import prepare_items
from .core.schemas import SCHEMA_PLUGINS, parse_rows_with_schema, validate_headers
from .shell import anki_csv_io, apkg_io, csv_io, manifest_io, media_io, report_io
from .shell.audio_io import realize_audio_requests


def run_app(config: AppConfig) -> None:
    raw_rows = csv_io.read_csv_rows(config.input)
    headers = list(raw_rows[0].keys()) if raw_rows else []

    schema_plugin = SCHEMA_PLUGINS[config.schema]
    deck_plugin = DECK_TYPE_PLUGINS[config.deck_type]

    validate_headers(headers, schema_plugin["required_headers"])
    items = parse_rows_with_schema(raw_rows, schema_plugin)
    prepared_items = prepare_items(items, config.freq_mode, config.level_mode)

    if config.level_mode == "report-only":
        report_io.print_level_report(prepared_items)

    if config.export_level_report:
        report_io.export_level_report_csv(prepared_items, config.export_level_report)

    csv_io.maybe_write_updated_csv(
        items=prepared_items,
        input_csv=config.input,
        write_updated_csv_path=config.write_updated_csv,
        in_place=config.in_place,
        backup=config.backup,
    )

    if config.diff_output:
        csv_io.export_diff_csv(prepared_items, config.diff_output)

    audio_requests = plan_audio_requests(prepared_items, config.cache_dir, config.voice)
    audio_results = realize_audio_requests(audio_requests, config.workers)
    audio_by_prompt = {r["item_prompt"]: r for r in audio_results}

    if config.export_anki_csv:
        anki_csv_io.export_anki_import_csv(prepared_items, audio_by_prompt, config.export_anki_csv)

    if config.export_media_dir:
        media_io.export_media_bundle(prepared_items, audio_by_prompt, config.export_media_dir)

    manifest_name = config.cache_manifest or default_manifest_name(config.input, config.deck_prefix, config.voice)
    manifest_payload = build_manifest_payload(prepared_items, audio_results, config)
    manifest_path = manifest_io.write_manifest(config.cache_dir, manifest_name, manifest_payload)
    print(f"\n🗂 Wrote cache manifest: {manifest_path}")

    if not config.no_cache_cleanup:
        manifest_io.cleanup_audio_cache_from_manifests(config.cache_dir)
    else:
        print("\n⏭ Skipped cache cleanup (--no-cache-cleanup)")

    if config.skip_apkg:
        print("\n⏭ Skipped .apkg generation (--skip-apkg)")
        return

    note_specs = build_note_specs(prepared_items, audio_by_prompt, deck_plugin, config.deck_prefix)
    apkg_io.write_apkg(note_specs, deck_plugin, config.output)
