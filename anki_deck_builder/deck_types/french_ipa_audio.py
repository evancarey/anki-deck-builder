import os

import genanki

from anki_deck_builder.deck_types.base import DeckType
from anki_deck_builder.domain.models import AudioBundle, StudyItem

MODEL_ID = 1091735999


class FrenchIpaAudioDeckType(DeckType):
    name = "french-ipa-audio"

    def create_model(self):
        return genanki.Model(
            MODEL_ID,
            "French IPA Audio Model",
            fields=[
                {"name": "French"},
                {"name": "IPA"},
                {"name": "English"},
                {"name": "Image"},
                {"name": "AudioSlow"},
                {"name": "AudioNormal"},
            ],
            templates=[
                {
                    "name": "Card 1",
                    "qfmt": '''
                        <div style="font-size:28px;">{{French}}</div>
                        <div style="font-size:18px; color:gray;"><i>{{IPA}}</i></div>
                        {{Image}}
                        <br>
                        {{AudioSlow}}<br>
                        {{AudioNormal}}
                    ''',
                    "afmt": '''
                        {{FrontSide}}
                        <hr id="answer">
                        <div style="font-size:24px;">{{English}}</div>
                    ''',
                },
            ],
        )

    def note_fields(self, item: StudyItem, audio: AudioBundle) -> list[str]:
        image_html = f'<img src="{os.path.basename(item.image)}">' if item.image else ""
        slow = f"[sound:{os.path.basename(audio.slow)}]" if audio.slow else ""
        normal = f"[sound:{os.path.basename(audio.normal)}]" if audio.normal else ""
        return [item.prompt, item.ipa, item.answer, image_html, slow, normal]

    def note_tags(self, item: StudyItem) -> list[str]:
        return item.tags

    def sort_key(self, item: StudyItem):
        freq_score = item.extra.get("freq_score", 0)
        token_count = item.extra.get("token_count", 0)
        return (-freq_score, token_count, item.prompt)

    def deck_name(self, deck_prefix: str, item: StudyItem) -> str:
        level = item.level or "Unsorted"
        return f"{deck_prefix}::{level}"

    def required_audio_modes(self) -> tuple[str, ...]:
        return ("slow", "normal")
