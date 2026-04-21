import hashlib
import json
import os
import re

from anki_deck_builder.config import AUDIO_CACHE_VERSION

CACHE_DIR = ".cache"
AUDIO_CACHE_DIR = os.path.join(CACHE_DIR, "audio")
MANIFEST_DIR = os.path.join(CACHE_DIR, "manifests")


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def ensure_cache_dirs():
    ensure_dir(CACHE_DIR)
    ensure_dir(AUDIO_CACHE_DIR)
    ensure_dir(MANIFEST_DIR)


def audio_identity_text(text: str, voice_id: str) -> str:
    return f"{AUDIO_CACHE_VERSION}|voice={voice_id}|text={text}"


def make_audio_cache_key(text: str, voice_id: str) -> str:
    return hashlib.md5(audio_identity_text(text, voice_id).encode("utf-8")).hexdigest()


def audio_cache_path_from_key(audio_key: str, speed: str) -> str:
    return os.path.join(AUDIO_CACHE_DIR, f"{audio_key}_{speed}.mp3")


def audio_cache_paths(text: str, voice_id: str) -> dict[str, str]:
    audio_key = make_audio_cache_key(text, voice_id)
    return {
        "key": audio_key,
        "slow": audio_cache_path_from_key(audio_key, "slow"),
        "normal": audio_cache_path_from_key(audio_key, "normal"),
    }


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
