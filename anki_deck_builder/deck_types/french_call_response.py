import os

import genanki

from anki_deck_builder.deck_types.base import DeckType
from anki_deck_builder.domain.models import AudioBundle, StudyItem

MODEL_ID = 2091735999


class FrenchCallResponseDeckType(DeckType):
    name = "french-call-response"

    def create_model(self):
        return genanki.Model(
            MODEL_ID,
            "French Call Response Model",
            fields=[
                {"name": "Call"},
                {"name": "Response"},
                {"name": "IPA"},
                {"name": "Audio"},
            ],
            templates=[
                {
                    "name": "Call -> Response",
                    "qfmt": '''
                        <div style="font-size:28px;">{{Call}}</div>
                        <div style="font-size:18px; color:gray;"><i>{{IPA}}</i></div>
                        {{Audio}}
                    ''',
                    "afmt": '''
                        {{FrontSide}}
                        <hr id="answer">
                        <div style="font-size:24px;">{{Response}}</div>
                    ''',
                },
            ],
        )

    def note_fields(self, item: StudyItem, audio: AudioBundle) -> list[str]:
        normal = f"[sound:{os.path.basename(audio.normal)}]" if audio.normal else ""
        return [item.prompt, item.answer, item.ipa, normal]

    def note_tags(self, item: StudyItem) -> list[str]:
        return item.tags

    def sort_key(self, item: StudyItem):
        return item.prompt

    def deck_name(self, deck_prefix: str, item: StudyItem) -> str:
        level = item.level or "CallResponse"
        return f"{deck_prefix}::{level}"

    def required_audio_modes(self) -> tuple[str, ...]:
        return ("normal",)
