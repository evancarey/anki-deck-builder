# anki-deck-builder

A refactor of the original single-file script into a **functional core + imperative shell** architecture.

## Highlights

- Functional core for schema parsing, level inference, tags, manifest planning, note planning
- Imperative shell for CSV IO, audio generation, media copying, manifest writing, and `.apkg` output
- Plugin registries for:
  - **schema plugins**
  - **deck type plugins**
- Works with:
  - `python -m anki_deck_builder ...`
  - `python -m anki_deck_builder.cli ...`
  - `anki-build ...` after `pip install -e .`

## Install

```bash
pip install -e .
```

## Current plugins

### Schema plugins
- `french-sentences`
- `french-call-response`

### Deck type plugins
- `french-ipa-audio`
- `french-call-response`

## Example

```bash
python -m anki_deck_builder \
  --input french_sentences.csv \
  --output french_sentences.apkg \
  --schema french-sentences \
  --deck-type french-ipa-audio
```

## Add a new schema plugin

Add a new parser function in `anki_deck_builder/core/schemas.py` and register it in `SCHEMA_PLUGINS`.

## Add a new deck type plugin

Add the pure note-field / deck-name logic in `anki_deck_builder/core/deck_types.py` and register it in `DECK_TYPE_PLUGINS`.
