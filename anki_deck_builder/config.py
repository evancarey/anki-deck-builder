from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    input: str
    output: str
    voice: str
    workers: int
    deck_prefix: str
    schema: str
    deck_type: str
    freq_mode: str
    level_mode: str
    export_level_report: str = ""
    write_updated_csv: str = ""
    in_place: bool = False
    backup: bool = False
    diff_output: str = ""
    export_anki_csv: str = ""
    export_media_dir: str = ""
    skip_apkg: bool = False
    cache_manifest: str = ""
    no_cache_cleanup: bool = False
    cache_dir: str = ".cache"
