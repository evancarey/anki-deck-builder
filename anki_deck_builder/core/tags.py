
def frequency_bucket(avg_zipf: float, min_zipf: float) -> str:
    if avg_zipf >= 5.2 and min_zipf >= 3.5:
        return "freq_common"
    if avg_zipf >= 4.2 and min_zipf >= 2.5:
        return "freq_mid"
    return "freq_rare"


def frequency_rank_tag(avg_zipf: float) -> str:
    bucket = int(max(0, min(8, round(avg_zipf))))
    return f"freq_zipf_{bucket}"


def build_tags(
    original_tags: tuple[str, ...],
    *,
    level: str,
    inferred_level: str,
    level_source: str,
    avg_zipf: float,
    min_zipf: float,
    raw_level: str,
) -> tuple[str, ...]:
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

    if raw_level and raw_level != inferred_level:
        auto_tags.append("level_differs_from_inference")
        auto_tags.append(f"level_inferred_{inferred_level.lower()}")

    return tuple(original_tags) + tuple(auto_tags)
