from __future__ import annotations

from .frequency import sentence_frequency_stats
from .levels import infer_level, resolve_level
from .models import PreparedItem, StudyItem
from .tags import build_tags


def prepare_item(item: StudyItem, freq_mode: str, level_mode: str) -> PreparedItem:
    stats = sentence_frequency_stats(item.prompt)
    avg_zipf = float(stats["avg_zipf"])
    min_zipf = float(stats["min_zipf"])
    token_count = int(stats["token_count"])

    inferred = infer_level(avg_zipf, min_zipf, token_count)
    level, level_source = resolve_level(item.raw_level, inferred, level_mode)
    tags = build_tags(
        item.tags,
        level=level,
        inferred_level=inferred,
        level_source=level_source,
        avg_zipf=avg_zipf,
        min_zipf=min_zipf,
        raw_level=item.raw_level,
    )
    freq_score = avg_zipf if freq_mode == "avg" else min_zipf

    return PreparedItem(
        prompt=item.prompt,
        answer=item.answer,
        ipa=item.ipa,
        image=item.image,
        level=level,
        raw_level=item.raw_level,
        inferred_level=inferred,
        level_source=level_source,
        tags=tags,
        extra={
            **item.extra,
            "avg_zipf": avg_zipf,
            "min_zipf": min_zipf,
            "max_zipf": float(stats["max_zipf"]),
            "token_count": token_count,
            "tokens": tuple(stats["tokens"]),
            "freq_score": freq_score,
            "original_tags": item.tags,
        },
    )


def prepare_items(items: list[StudyItem], freq_mode: str, level_mode: str) -> list[PreparedItem]:
    return [prepare_item(item, freq_mode, level_mode) for item in items]
