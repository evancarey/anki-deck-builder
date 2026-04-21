from collections import defaultdict
import os

import genanki

from anki_deck_builder.domain.ids import deterministic_deck_id, make_note_guid
from anki_deck_builder.domain.models import AudioBundle, StudyItem


def write_apkg(items: list[StudyItem], deck_type, output_file: str, audio_lookup: dict[str, AudioBundle], deck_prefix: str):
    model = deck_type.create_model()
    grouped: dict[str, list[StudyItem]] = defaultdict(list)
    media_files = set()

    for item in items:
        grouped[deck_type.deck_name(deck_prefix, item)].append(item)

    decks = []
    for deck_name, deck_items in grouped.items():
        deck = genanki.Deck(deterministic_deck_id(deck_name), deck_name)
        for item in sorted(deck_items, key=deck_type.sort_key):
            audio = audio_lookup[item.prompt]
            note = genanki.Note(
                model=model,
                fields=deck_type.note_fields(item, audio),
                tags=deck_type.note_tags(item),
                guid=make_note_guid(item.prompt, item.answer),
            )
            deck.add_note(note)

            if audio.slow and os.path.exists(audio.slow):
                media_files.add(audio.slow)
            if audio.normal and os.path.exists(audio.normal):
                media_files.add(audio.normal)
            if item.image and os.path.exists(item.image):
                media_files.add(item.image)

        decks.append(deck)

    package = genanki.Package(decks)
    package.media_files = sorted(media_files)
    package.write_to_file(output_file)

    print(f"\n✅ Decks created: {output_file}")
    print("\nDeck summary:")
    for deck_name, deck_items in sorted(grouped.items()):
        print(f"  - {deck_name}: {len(deck_items)} notes")
