from __future__ import annotations

from collections import defaultdict

import genanki

from ..core.deck_types import deterministic_deck_id
from ..core.models import NoteSpec


def create_model(deck_plugin: dict):
    return genanki.Model(
        deck_plugin["model_id"],
        deck_plugin["model_name"],
        fields=[{"name": name} for name in deck_plugin["fields"]],
        templates=deck_plugin["templates"],
    )


def write_apkg(note_specs: list[NoteSpec], deck_plugin: dict, output_file: str) -> None:
    model = create_model(deck_plugin)
    grouped: dict[str, list[NoteSpec]] = defaultdict(list)
    media_files: set[str] = set()
    for spec in note_specs:
        grouped[spec.deck_name].append(spec)
        media_files.update(spec.media_files)

    decks = []
    for deck_name in sorted(grouped.keys()):
        deck = genanki.Deck(deterministic_deck_id(deck_name), deck_name)
        for spec in grouped[deck_name]:
            note = genanki.Note(model=model, fields=list(spec.fields), tags=list(spec.tags), guid=spec.guid)
            deck.add_note(note)
        decks.append(deck)

    package = genanki.Package(decks)
    package.media_files = sorted(media_files)
    package.write_to_file(output_file)

    print(f"\n✅ Decks created: {output_file}")
    print("\nDeck summary:")
    for deck_name in sorted(grouped.keys()):
        print(f"  - {deck_name}: {len(grouped[deck_name])} notes")
