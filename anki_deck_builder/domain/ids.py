import hashlib


def make_note_guid(prompt: str, answer: str) -> str:
    return hashlib.md5((prompt + answer).encode("utf-8")).hexdigest()


def deterministic_deck_id(name: str) -> int:
    digest = hashlib.md5(name.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)
