# Anki Deck Builder (French Sentences)

Generate high-quality Anki decks from French sentence CSVs with:

- 🇫🇷 Text-to-speech audio (slow + normal)
- 📊 Frequency-based ordering
- 🧠 CEFR level inference
- ⚡ Shared audio cache with manifest-based cleanup
- 📦 Flexible export (APKG, CSV, media-only)

This project is optimized for iterative workflows and large deck management.

---

## 🚀 Quick Start

From your SPA / project repo:

```bash
python build_deck.py   --input french_sentences_updated.csv   --export-anki-csv update.csv   --export-media-dir media   --skip-apkg
```

---

## 📥 Input CSV Format

Expected columns:

- `French` (required)
- `IPA` (optional)
- `English` (required)
- `Image` (optional)
- `Level` (optional)

---

## 📤 Outputs

Depending on options, the script can generate:

- `.apkg` (Anki deck)
- Anki import CSV
- Media folder (audio/images)
- Updated CSV (levels + tags)
- Diff reports
- Level analysis report

---

## ⚙️ Command Options

### General

- `--input` Input CSV
- `--output` Output `.apkg`
- `--voice` TTS voice
- `--workers` Parallel processing threads
- `--deck-prefix` Deck naming prefix

---

### 📊 Frequency Scoring

- `--freq-mode avg` → average word frequency (default)
- `--freq-mode min` → rarest word (better difficulty signal)

---

### 🧠 Level Modes

- `respect-existing` (default) → keep existing levels, fill blanks
- `recompute-all` → ignore CSV levels and recompute everything
- `report-only` → no changes, just analysis

---

### 📄 CSV + Reporting

- `--write-updated-csv` Write updated CSV
- `--in-place` Modify input CSV directly
- `--backup` Create timestamp backup (recommended)
- `--diff-output` Row-level changes report
- `--export-level-report` Export level comparison CSV

---

### 📦 Anki Export

- `--export-anki-csv` CSV formatted for Anki
- `--export-media-dir` Folder for audio/images
- `--skip-apkg` Skip `.apkg` build (faster iteration)

---

### 🎧 Shared Audio Cache

- `--cache-manifest` Custom manifest name
- `--no-cache-cleanup` Disable cleanup

#### Behavior

- Audio is stored in `.cache/`
- Cache key is **independent of English text**
- Same sentence won't regenerate audio unnecessarily
- Manifest tracks "in-use" audio files
- Orphaned audio is automatically cleaned up

---

## 📁 Project Structure (Recommended)

```
project/
├── build_deck.py
├── scripts/
│   └── build_and_sync.sh   # your deploy script
├── .cache/                 # shared audio cache
├── media/                  # generated media (temp)
├── french_sentences_updated.csv
├── update.csv
└── README.md
```

---

## 🔄 Typical Workflow

### 1. Generate Deck Data

```bash
python build_deck.py   --input french_sentences_updated.csv   --export-anki-csv update.csv   --export-media-dir media   --skip-apkg
```

---

### 2. Import into Anki

- Import `update.csv`
- Ensure fields are mapped correctly
- Deck should reuse existing notes (no duplicates if GUIDs stable)

---

### 3. Copy Media

Copy or move files:

```
media/* → Anki collection.media/
```

No need to keep `media/` after import.

---

## 🧠 Cache Strategy (Important)

This project uses a **shared cache with stable identity**:

- Audio key does NOT change when English changes
- Prevents unnecessary regeneration
- Keeps decks consistent across revisions

### Cleanup

- Automatic via manifest tracking
- Safe across multiple decks if manifest names differ
- Disable with `--no-cache-cleanup` if needed

---

## ⚠️ Common Pitfalls

### Duplicate Notes

- Ensure note GUID logic is stable
- Do not change key identity fields unintentionally

---

### Audio Confusion

- `.cache/` = persistent shared audio
- `media/` = export-only (for Anki import)

---

### Unexpected Note Counts

- Each CSV row = 1 note
- Multiple cards can be generated depending on note type in Anki

---

## 🧪 Useful Commands

### Recompute All Levels

```bash
python build_deck.py --input data.csv --level-mode recompute-all
```

---

### Safe In-Place Update

```bash
python build_deck.py   --input data.csv   --in-place   --backup
```

---

### Debug Changes

```bash
python build_deck.py   --input data.csv   --diff-output diff.csv
```

---

## 📌 Design Goals

- Deterministic outputs
- Fast iteration cycles
- Stable audio caching
- Clean separation of:
  - source data
  - generated media
  - persistent cache

---

## ✅ Summary

This tool gives you a reliable pipeline for:

- Building large French sentence decks
- Maintaining stable Anki imports
- Avoiding duplicate audio generation
- Iterating quickly without breaking existing decks
