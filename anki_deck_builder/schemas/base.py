from abc import ABC, abstractmethod

from anki_deck_builder.domain.models import SourceRow, StudyItem


class InputSchema(ABC):
    name: str

    @abstractmethod
    def validate_headers(self, headers: list[str]) -> None:
        raise NotImplementedError

    @abstractmethod
    def to_study_item(self, row: SourceRow) -> StudyItem:
        raise NotImplementedError
