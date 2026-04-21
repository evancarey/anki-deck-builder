from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StudyItem:
    prompt: str
    answer: str
    ipa: str = ""
    image: str = ""
    raw_level: str = ""
    tags: tuple[str, ...] = ()
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PreparedItem:
    prompt: str
    answer: str
    ipa: str
    image: str
    level: str
    raw_level: str
    inferred_level: str
    level_source: str
    tags: tuple[str, ...]
    extra: dict[str, Any]


@dataclass(frozen=True)
class NoteSpec:
    deck_name: str
    guid: str
    fields: tuple[str, ...]
    tags: tuple[str, ...]
    media_files: tuple[str, ...]
