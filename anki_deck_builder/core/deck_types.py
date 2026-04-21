from __future__ import annotations

import hashlib
import os
from collections import defaultdict

from .models import NoteSpec, PreparedItem


def make_note_guid(prompt: str, answer: str) -> str:
    return hashlib.md5((prompt + answer).encode("utf-8")).hexdigest()


def deterministic_deck_id(name: str) -> int:
    digest = hashlib.md5(name.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def french_ipa_audio_note_fields(item: PreparedItem, audio: dict[str, str]) -> tuple[str, ...]:
    image_html = f'<img src="{os.path.basename(item.image)}">' if item.image else ""
    return (
        item.prompt,
        item.ipa,
        item.answer,
        image_html,
        f"[sound:{os.path.basename(audio['slow_path'])}]",
        f"[sound:{os.path.basename(audio['normal_path'])}]",
    )


def french_ipa_audio_deck_name(deck_prefix: str, item: PreparedItem) -> str:
    return f"{deck_prefix}::{item.level}"


def french_call_response_note_fields(item: PreparedItem, audio: dict[str, str]) -> tuple[str, ...]:
    return (
        item.prompt,
        item.answer,
        item.ipa,
        f"[sound:{os.path.basename(audio['normal_path'])}]",
    )


def french_call_response_deck_name(deck_prefix: str, item: PreparedItem) -> str:
    return f"{deck_prefix}::CallResponse"


DECK_TYPE_PLUGINS = {
    "french-ipa-audio": {
        "model_name": "French IPA Audio Model",
        "model_id": 1091735999,
        "fields": ("French", "IPA", "English", "Image", "AudioSlow", "AudioNormal"),
        "templates": [
            {
                "name": "Card 1",
                "qfmt": """
                    <div style=\"font-size:28px;\">{{French}}</div>
                    <div style=\"font-size:18px; color:gray;\"><i>{{IPA}}</i></div>
                    {{Image}}<br>
                    {{AudioSlow}}<br>
                    {{AudioNormal}}
                """,
                "afmt": """
                    {{FrontSide}}
                    <hr id=\"answer\">
                    <div style=\"font-size:24px;\">{{English}}</div>
                """,
            }
        ],
        "note_fields": french_ipa_audio_note_fields,
        "deck_name": french_ipa_audio_deck_name,
        "sort_key": lambda item: (-item.extra["freq_score"], item.extra["token_count"], item.prompt),
    },
    "french-call-response": {
        "model_name": "French Call Response Model",
        "model_id": 2091735999,
        "fields": ("Call", "Response", "IPA", "Audio"),
        "templates": [
            {
                "name": "Card 1",
                "qfmt": """
                    <div style=\"font-size:28px;\">{{Call}}</div>
                    <div style=\"font-size:18px; color:gray;\"><i>{{IPA}}</i></div>
                    {{Audio}}
                """,
                "afmt": """
                    {{FrontSide}}
                    <hr id=\"answer\">
                    <div style=\"font-size:24px;\">{{Response}}</div>
                """,
            }
        ],
        "note_fields": french_call_response_note_fields,
        "deck_name": french_call_response_deck_name,
        "sort_key": lambda item: item.prompt,
    },
}


def build_note_specs(
    items: list[PreparedItem],
    audio_by_prompt: dict[str, dict[str, str]],
    deck_plugin: dict,
    deck_prefix: str,
) -> list[NoteSpec]:
    note_specs: list[NoteSpec] = []
    note_fields_fn = deck_plugin["note_fields"]
    deck_name_fn = deck_plugin["deck_name"]

    for item in items:
        audio = audio_by_prompt[item.prompt]
        media_files = [audio["normal_path"]]
        if "slow_path" in audio:
            media_files.append(audio["slow_path"])
        if item.image:
            media_files.append(item.image)

        note_specs.append(
            NoteSpec(
                deck_name=deck_name_fn(deck_prefix, item),
                guid=make_note_guid(item.prompt, item.answer),
                fields=note_fields_fn(item, audio),
                tags=item.tags,
                media_files=tuple(media_files),
            )
        )

    sort_key = deck_plugin["sort_key"]
    grouped: dict[str, list[NoteSpec]] = defaultdict(list)
    item_by_guid = {make_note_guid(item.prompt, item.answer): item for item in items}
    for spec in note_specs:
        grouped[spec.deck_name].append(spec)

    sorted_specs: list[NoteSpec] = []
    for deck_name in sorted(grouped.keys()):
        deck_specs = grouped[deck_name]
        deck_specs.sort(key=lambda spec: sort_key(item_by_guid[spec.guid]))
        sorted_specs.extend(deck_specs)
    return sorted_specs
