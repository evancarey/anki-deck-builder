from __future__ import annotations

import json
import os
import re


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def manifest_dir(cache_dir: str) -> str:
    return os.path.join(cache_dir, "manifests")


def audio_dir(cache_dir: str) -> str:
    return os.path.join(cache_dir, "audio")


def manifest_path(cache_dir: str, manifest_name: str) -> str:
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", manifest_name).strip("._-") or "default"
    return os.path.join(manifest_dir(cache_dir), f"{safe_name}.json")


def write_manifest(cache_dir: str, manifest_name: str, payload: dict) -> str:
    ensure_dir(cache_dir)
    ensure_dir(manifest_dir(cache_dir))
    ensure_dir(audio_dir(cache_dir))
    path = manifest_path(cache_dir, manifest_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return path


def load_all_manifest_references(cache_dir: str) -> set[str]:
    ensure_dir(manifest_dir(cache_dir))
    referenced: set[str] = set()
    for name in os.listdir(manifest_dir(cache_dir)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(manifest_dir(cache_dir), name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            for relpath in payload.get("audio_files", []):
                referenced.add(os.path.basename(relpath))
        except Exception as exc:
            print(f"⚠️ Could not read manifest {path}: {exc}")
    return referenced


def cleanup_audio_cache_from_manifests(cache_dir: str) -> None:
    ensure_dir(audio_dir(cache_dir))
    referenced = load_all_manifest_references(cache_dir)
    removed = 0
    kept = 0
    for name in os.listdir(audio_dir(cache_dir)):
        if not name.lower().endswith(".mp3"):
            continue
        path = os.path.join(audio_dir(cache_dir), name)
        if name in referenced:
            kept += 1
            continue
        try:
            os.remove(path)
            removed += 1
        except Exception as exc:
            print(f"⚠️ Could not remove cache file {path}: {exc}")
    print(f"\n🧹 Cache cleanup complete: kept {kept}, removed {removed} orphaned audio files")
