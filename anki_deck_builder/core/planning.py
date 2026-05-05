from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Iterable

from ..config import AppConfig
from .models import PreparedItem

AUDIO_CACHE_VERSION = "v3"


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


def make_request_id(item: PreparedItem) -> str:
    return hashlib.md5((item.prompt + item.answer).encode("utf-8")).hexdigest()


def plan_audio_requests(items: list[PreparedItem], cache_dir: str, voice_id: str) -> list[dict]:
    requests: list[dict] = []
    for item in items:
        source_schema = item.extra.get("source_schema", "french-sentences")
        request = {
            "request_id": make_request_id(item),
            "voice_id": voice_id,
            "source_schema": source_schema,
            "audio_parts": {},
        }
        if source_schema == "french-call-response":
            call_text = item.extra.get("call_french", item.prompt)
            response_text = item.extra.get("response_french", item.answer)
            request["audio_parts"] = {
                "call": {
                    "text": call_text,
                    **audio_paths(cache_dir, call_text, voice_id),
                },
                "response": {
                    "text": response_text,
                    **audio_paths(cache_dir, response_text, voice_id),
                },
            }
        else:
            request["audio_parts"] = {
                "main": {
                    "text": item.prompt,
                    **audio_paths(cache_dir, item.prompt, voice_id),
                }
            }
        requests.append(request)
    return requests


def iter_audio_paths(audio_request: dict) -> Iterable[str]:
    for part in audio_request.get("audio_parts", {}).values():
        yield part["slow_path"]
        yield part["normal_path"]


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


def build_manifest_payload(items: list[PreparedItem], audio_results: list[dict], config: AppConfig) -> dict:
    audio_files: list[str] = []
    audio_keys: list[str] = []

    for result in audio_results:
        for part in result.get("audio_parts", {}).values():
            audio_keys.append(part["cache_key"])
            audio_files.append(os.path.relpath(part["slow_path"], config.cache_dir))
            audio_files.append(os.path.relpath(part["normal_path"], config.cache_dir))

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
