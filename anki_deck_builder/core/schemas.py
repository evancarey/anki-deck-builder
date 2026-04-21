from __future__ import annotations

from .models import StudyItem


def _split_tags(value: str) -> tuple[str, ...]:
    return tuple(t.strip() for t in (value or "").split(",") if t.strip())


def parse_french_sentences_row(row: dict[str, str]) -> StudyItem:
    return StudyItem(
        prompt=row["French"],
        answer=row["English"],
        ipa=(row.get("IPA") or "").strip(),
        image=(row.get("Image") or "").strip(),
        raw_level=(row.get("Level") or "").strip(),
        tags=_split_tags(row.get("Tags") or ""),
        extra={"source_schema": "french-sentences"},
    )


def parse_call_response_row(row: dict[str, str]) -> StudyItem:
    return StudyItem(
        prompt=row["Call"],
        answer=row["Response"],
        ipa=(row.get("IPA") or "").strip(),
        image=(row.get("Image") or "").strip(),
        raw_level=(row.get("Level") or "").strip(),
        tags=_split_tags(row.get("Tags") or ""),
        extra={"source_schema": "french-call-response"},
    )


SCHEMA_PLUGINS = {
    "french-sentences": {
        "required_headers": ("French", "English"),
        "parse_row": parse_french_sentences_row,
    },
    "french-call-response": {
        "required_headers": ("Call", "Response"),
        "parse_row": parse_call_response_row,
    },
}


def validate_headers(headers: list[str], required_headers: tuple[str, ...]) -> None:
    missing = [name for name in required_headers if name not in headers]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def parse_rows_with_schema(rows: list[dict[str, str]], schema_plugin: dict) -> list[StudyItem]:
    parser = schema_plugin["parse_row"]
    return [parser(row) for row in rows]
