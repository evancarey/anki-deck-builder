from abc import ABC, abstractmethod

from anki_deck_builder.domain.models import AudioBundle, StudyItem


class DeckType(ABC):
    name: str

    @abstractmethod
    def create_model(self):
        raise NotImplementedError

    @abstractmethod
    def note_fields(self, item: StudyItem, audio: AudioBundle) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def note_tags(self, item: StudyItem) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def sort_key(self, item: StudyItem):
        raise NotImplementedError

    @abstractmethod
    def deck_name(self, deck_prefix: str, item: StudyItem) -> str:
        raise NotImplementedError

    def required_audio_modes(self) -> tuple[str, ...]:
        return ("slow", "normal")
