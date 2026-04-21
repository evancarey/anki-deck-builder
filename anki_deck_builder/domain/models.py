from dataclasses import dataclass, field
from typing import Any


@dataclass
class SourceRow:
    data: dict[str, Any]


@dataclass
class StudyItem:
    prompt: str
    answer: str
    ipa: str = ""
    image: str = ""
    level: str = ""
    raw_level: str = ""
    inferred_level: str = ""
    level_source: str = ""
    tags: list[str] = field(default_factory=list)
    original_tags: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class AudioBundle:
    key: str = ""
    slow: str = ""
    normal: str = ""
