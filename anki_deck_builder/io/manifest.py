import json
import os
import re
from datetime import datetime, timezone

from anki_deck_builder.audio.cache import CACHE_DIR, AUDIO_CACHE_DIR, MANIFEST_DIR, ensure_cache_dirs


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def manifest_path(manifest_name: str) -> str:
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", manifest_name).strip("._-")
    if not safe_name:
        safe_name = "default"
    return os.path.join(MANIFEST_DIR, f"{safe_name}.json")


def write_manifest(manifest_name: str, payload: dict) -> str:
    ensure_cache_dirs()
    path = manifest_path(manifest_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return path


def load_all_manifest_references() -> set[str]:
    ensure_cache_dirs()
    referenced = set()
    for name in os.listdir(MANIFEST_DIR):
        if not name.endswith(".json"):
            continue
        path = os.path.join(MANIFEST_DIR, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            for relpath in payload.get("audio_files", []):
                referenced.add(os.path.basename(relpath))
        except Exception as e:
            print(f"⚠️ Could not read manifest {path}: {e}")
    return referenced


def cleanup_audio_cache_from_manifests():
    ensure_cache_dirs()
    referenced = load_all_manifest_references()

    removed = 0
    kept = 0
    for name in os.listdir(AUDIO_CACHE_DIR):
        if not name.lower().endswith(".mp3"):
            continue
        path = os.path.join(AUDIO_CACHE_DIR, name)
        if name in referenced:
            kept += 1
            continue
        try:
            os.remove(path)
            removed += 1
        except Exception as e:
            print(f"⚠️ Could not remove cache file {path}: {e}")

    print(f"\n🧹 Cache cleanup complete: kept {kept}, removed {removed} orphaned audio files")


def build_manifest_payload(items, input_csv: str, output_file: str, deck_prefix: str, voice_id: str, audio_lookup) -> dict:
    audio_files = set()
    audio_keys = set()

    for item in items:
        bundle = audio_lookup[item.prompt]
        audio_keys.add(bundle.key)
        if bundle.slow:
            audio_files.add(os.path.relpath(bundle.slow, CACHE_DIR))
        if bundle.normal:
            audio_files.add(os.path.relpath(bundle.normal, CACHE_DIR))

    return {
        "version": 1,
        "updated_at": utc_now_iso(),
        "input_csv": os.path.abspath(input_csv),
        "output_file": os.path.abspath(output_file),
        "deck_prefix": deck_prefix,
        "voice": voice_id,
        "audio_keys": sorted(audio_keys),
        "audio_files": sorted(audio_files),
    }
