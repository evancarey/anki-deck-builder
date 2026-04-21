def infer_level(avg_zipf: float, min_zipf: float, token_count: int) -> str:
    if avg_zipf >= 5.2 and min_zipf >= 3.2 and token_count <= 8:
        return "A1"
    if avg_zipf >= 4.7 and min_zipf >= 2.5 and token_count <= 12:
        return "A2"
    if avg_zipf >= 4.0 and min_zipf >= 1.8 and token_count <= 18:
        return "B1"
    return "B2"


def resolve_level(raw_level: str, inferred_level: str, level_mode: str) -> tuple[str, str]:
    raw_level = (raw_level or "").strip()

    if level_mode == "recompute-all":
        return inferred_level, "auto"

    if level_mode in {"respect-existing", "report-only"}:
        if raw_level:
            return raw_level, "manual"
        return inferred_level, "auto"

    raise ValueError(f"Unsupported level_mode: {level_mode}")
