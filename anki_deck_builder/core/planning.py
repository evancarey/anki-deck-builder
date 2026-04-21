from __future__ import annotations

import hashlib
import json
import os
import re

from ..config import AppConfig
from .models import PreparedItem

AUDIO_CACHE_VERSION = "v2"


def make_audio_cache_key(text: str, voice_id: str) -> str:
    basis = f"{AUDIO_CACHE_VERSION}|voice={voice_id}|text={text}"
    return hashlib.md5(basis.encode("utf-8")).hexdigest()


def audio_paths(cache_dir: str, text: str, voice_id: str) -> dict[str, str]:
    key = make_audio_cache_key(text, voice_id)
    audio_dir = os.path.join(cache_dir, "audio")
    return {
        "cache_key": key,
        "slow_path": os.path.join(audio_dir, f"{key}_slow.mp3"),
        "normal_path": os.path.join(audio_dir, f"{key}_normal.mp3"),
    }


def plan_audio_requests(items: list[PreparedItem], cache_dir: str, voice_id: str) -> list[dict[str, str]]:
    return [
        {
            "item_prompt": item.prompt,
            "voice_id": voice_id,
            **audio_paths(cache_dir, item.prompt, voice_id),
        }
        for item in items
    ]


def default_manifest_name(input_csv: str, deck_prefix: str, voice_id: str) -> str:
    basis = json.dumps(
        {
            "input": os.path.abspath(input_csv),
            "deck_prefix": deck_prefix,
            "voice": voice_id,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    digest = hashlib.md5(basis.encode("utf-8")).hexdigest()[:16]
    safe_prefix = re.sub(r"[^A-Za-z0-9._-]+", "_", deck_prefix).strip("._-") or "deck"
    return f"{safe_prefix}_{voice_id}_{digest}"


def build_manifest_payload(items: list[PreparedItem], audio_results: list[dict[str, str]], config: AppConfig) -> dict:
    audio_files: list[str] = []
    audio_keys: list[str] = []

    for result in audio_results:
        audio_keys.append(result["cache_key"])
        audio_files.append(os.path.relpath(result["slow_path"], config.cache_dir))
        audio_files.append(os.path.relpath(result["normal_path"], config.cache_dir))

    return {
        "version": 1,
        "input_csv": os.path.abspath(config.input),
        "output_file": os.path.abspath(config.output),
        "deck_prefix": config.deck_prefix,
        "voice": config.voice,
        "audio_cache_version": AUDIO_CACHE_VERSION,
        "audio_keys": sorted(audio_keys),
        "audio_files": sorted(audio_files),
        "levels": sorted({item.level for item in items}),
    }
