from dataclasses import dataclass

DEFAULT_DECK_PREFIX = "French"
AUDIO_CACHE_VERSION = "v2"

@dataclass
class AppConfig:
    input_csv: str
    output_file: str
    voice_id: str
    workers: int
    deck_prefix: str
    schema_name: str
    deck_type_name: str
    freq_mode: str
    level_mode: str
    export_level_report: str
    write_updated_csv_path: str
    in_place: bool
    backup: bool
    diff_output: str
    export_anki_csv_path: str
    export_media_dir: str
    skip_apkg: bool
    cache_manifest: str
    no_cache_cleanup: bool
