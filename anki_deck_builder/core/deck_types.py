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



def french_ipa_audio_note_fields(item: PreparedItem, audio: dict) -> tuple[str, ...]:
    image_html = f'<img src="{os.path.basename(item.image)}">' if item.image else ""
    main_audio = audio["audio_parts"]["main"]
    return (
        item.prompt,
        item.ipa,
        item.answer,
        image_html,
        f"[sound:{os.path.basename(main_audio['slow_path'])}]",
        f"[sound:{os.path.basename(main_audio['normal_path'])}]",
    )



def french_ipa_audio_deck_name(deck_prefix: str, item: PreparedItem) -> str:
    return f"{deck_prefix}::{item.level}"



def french_call_response_note_fields(item: PreparedItem, audio: dict) -> tuple[str, ...]:
    call_french = item.extra.get("call_french", item.prompt)
    call_ipa = item.extra.get("call_ipa", item.ipa)
    call_english = item.extra.get("call_english", "")
    response_french = item.extra.get("response_french", item.answer)
    response_ipa = item.extra.get("response_ipa", "")
    response_english = item.extra.get("response_english", "")
    call_audio = audio["audio_parts"]["call"]
    response_audio = audio["audio_parts"]["response"]
    return (
        call_french,
        call_ipa,
        call_english,
        response_french,
        response_ipa,
        response_english,
        f"[sound:{os.path.basename(call_audio['slow_path'])}]",
        f"[sound:{os.path.basename(call_audio['normal_path'])}]",
        f"[sound:{os.path.basename(response_audio['slow_path'])}]",
        f"[sound:{os.path.basename(response_audio['normal_path'])}]",
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
                    <div style="font-size:28px;"><i>{{IPA}}</i></div>
                    {{Image}}<br>
                    {{AudioSlow}}<br>
                    {{AudioNormal}}
                """,
                "afmt": """
                    {{FrontSide}}
                    <hr id="answer">
                    <div style="font-size:24px;">{{French}}</div>
                    <div style="font-size:18px;color:grey">{{English}}</div>
                """,
            }
        ],
        "note_fields": french_ipa_audio_note_fields,
        "deck_name": french_ipa_audio_deck_name,
        "sort_key": lambda item: (-item.extra["freq_score"], item.extra["token_count"], item.prompt),
    },
    "french-call-response": {
        "model_name": "French Call Response Model v3",
        "model_id": 2091736002,
        "fields": (
            "CallFrench",
            "CallIPA",
            "CallEnglish",
            "ResponseFrench",
            "ResponseIPA",
            "ResponseEnglish",
            "CallAudioSlow",
            "CallAudioFast",
            "ResponseAudioSlow",
            "ResponseAudioFast",
        ),
        "templates": [
            {
                "name": "Card 1",
                "qfmt": """
                    <div style="font-size:28px;"><i>{{CallIPA}}</i></div>
                    <br>
                    <div>{{CallAudioSlow}}</div>
                    <div>{{CallAudioFast}}</div>
                """,
                "afmt": """
                    {{FrontSide}}
                    <hr id="answer">
                    <div style="font-size:24px;">{{CallFrench}}</div>
                    <div style="font-size:18px; color:gray;">{{CallEnglish}}</div>
                    <br>
                    <div style="font-size:24px;">{{ResponseFrench}}</div>
                    <div style="font-size:18px;"><i>{{ResponseIPA}}</i></div>
                    <div style="font-size:18px; color:gray;">{{ResponseEnglish}}</div>
                    <br>
                    <div>{{ResponseAudioSlow}}</div>
                    <div>{{ResponseAudioFast}}</div>
                """,
            }
        ],
        "note_fields": french_call_response_note_fields,
        "deck_name": french_call_response_deck_name,
        "sort_key": lambda item: (item.prompt, item.answer),
    },
}



def build_note_specs(
    items: list[PreparedItem],
    audio_by_request_id: dict[str, dict],
    deck_plugin: dict,
    deck_prefix: str,
) -> list[NoteSpec]:
    note_specs: list[NoteSpec] = []
    note_fields_fn = deck_plugin["note_fields"]
    deck_name_fn = deck_plugin["deck_name"]

    for item in items:
        request_id = make_note_guid(item.prompt, item.answer)
        audio = audio_by_request_id[request_id]
        media_files: list[str] = []
        for part in audio.get("audio_parts", {}).values():
            media_files.append(part["slow_path"])
            media_files.append(part["normal_path"])
        if item.image:
            media_files.append(item.image)

        note_specs.append(
            NoteSpec(
                deck_name=deck_name_fn(deck_prefix, item),
                guid=request_id,
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
