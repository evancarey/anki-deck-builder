from __future__ import annotations

import re

from wordfreq import zipf_frequency


def tokenize_french(text: str) -> list[str]:
    text = text.lower()
    tokens = re.findall(r"[a-zàâçéèêëîïôûùüÿñæœ'-]+", text, flags=re.IGNORECASE)
    normalized: list[str] = []
    for token in tokens:
        token = token.strip("-'")
        if not token:
            continue
        parts = re.split(r"[']", token)
        for part in parts:
            part = part.strip("- ")
            if part:
                normalized.append(part)
    return normalized


def word_zipf(token: str) -> float:
    return zipf_frequency(token, "fr")


def sentence_frequency_stats(text: str) -> dict[str, object]:
    tokens = tokenize_french(text)
    if not tokens:
        return {
            "tokens": [],
            "token_count": 0,
            "avg_zipf": 0.0,
            "min_zipf": 0.0,
            "max_zipf": 0.0,
        }

    freqs = [word_zipf(token) for token in tokens]
    return {
        "tokens": tokens,
        "token_count": len(tokens),
        "avg_zipf": sum(freqs) / len(freqs),
        "min_zipf": min(freqs),
        "max_zipf": max(freqs),
    }
