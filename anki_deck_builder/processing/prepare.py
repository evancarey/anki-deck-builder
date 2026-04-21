from anki_deck_builder.domain.models import StudyItem
from anki_deck_builder.processing.frequency import (
    frequency_bucket,
    frequency_rank_tag,
    sentence_frequency_stats,
)
from anki_deck_builder.processing.levels import infer_level, resolve_level


def prepare_item(item: StudyItem, freq_mode: str, level_mode: str) -> StudyItem:
    stats = sentence_frequency_stats(item.prompt)
    avg_zipf = stats["avg_zipf"]
    min_zipf = stats["min_zipf"]
    token_count = stats["token_count"]

    inferred_level = infer_level(avg_zipf, min_zipf, token_count)
    level, level_source = resolve_level(item.raw_level, inferred_level, level_mode)

    auto_tags = [
        frequency_bucket(avg_zipf, min_zipf),
        frequency_rank_tag(avg_zipf),
        f"level_{level.lower()}",
        f"level_source_{level_source}",
    ]

    if level_source == "auto":
        auto_tags.append(f"level_auto_{inferred_level.lower()}")
    else:
        auto_tags.append("level_manual")

    if item.raw_level and item.raw_level != inferred_level:
        auto_tags.append("level_differs_from_inference")
        auto_tags.append(f"level_inferred_{inferred_level.lower()}")

    item.level = level
    item.inferred_level = inferred_level
    item.level_source = level_source
    item.tags = list(item.tags) + auto_tags

    item.extra.update(
        {
            "avg_zipf": avg_zipf,
            "min_zipf": min_zipf,
            "max_zipf": stats["max_zipf"],
            "token_count": token_count,
            "tokens": " ".join(stats["tokens"]),
            "freq_score": avg_zipf if freq_mode == "avg" else min_zipf,
        }
    )
    return item
