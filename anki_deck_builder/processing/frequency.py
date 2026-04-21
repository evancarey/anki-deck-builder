import re

from wordfreq import zipf_frequency


def tokenize_french(text: str) -> list[str]:
    text = text.lower()
    tokens = re.findall(r"[a-zàâçéèêëîïôûùüÿñæœ'-]+", text, flags=re.IGNORECASE)
    normalized = []
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


def sentence_frequency_stats(text: str) -> dict:
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


def frequency_bucket(avg_zipf: float, min_zipf: float) -> str:
    if avg_zipf >= 5.2 and min_zipf >= 3.5:
        return "freq_common"
    if avg_zipf >= 4.2 and min_zipf >= 2.5:
        return "freq_mid"
    return "freq_rare"


def frequency_rank_tag(avg_zipf: float) -> str:
    bucket = int(max(0, min(8, round(avg_zipf))))
    return f"freq_zipf_{bucket}"
