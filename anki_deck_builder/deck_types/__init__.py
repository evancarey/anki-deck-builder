from .french_call_response import FrenchCallResponseDeckType
from .french_ipa_audio import FrenchIpaAudioDeckType


def available_deck_types():
    return {
        FrenchIpaAudioDeckType.name: FrenchIpaAudioDeckType,
        FrenchCallResponseDeckType.name: FrenchCallResponseDeckType,
    }


def get_deck_type(name: str):
    deck_types = available_deck_types()
    if name not in deck_types:
        raise ValueError(f"Unknown deck type plugin: {name}")
    return deck_types[name]()
