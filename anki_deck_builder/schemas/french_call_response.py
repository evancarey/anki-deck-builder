from anki_deck_builder.domain.models import SourceRow, StudyItem
from anki_deck_builder.schemas.base import InputSchema


class FrenchCallResponseSchema(InputSchema):
    name = "french-call-response"
    required_headers = ["Call", "Response"]

    def validate_headers(self, headers: list[str]) -> None:
        missing = [h for h in self.required_headers if h not in headers]
        if missing:
            raise ValueError(f"Missing required columns for {self.name}: {missing}")

    def to_study_item(self, row: SourceRow) -> StudyItem:
        data = row.data
        raw_tags = [t.strip() for t in (data.get("Tags") or "").split(",") if t.strip()]
        return StudyItem(
            prompt=data["Call"],
            answer=data["Response"],
            ipa=(data.get("IPA") or "").strip(),
            image=(data.get("Image") or "").strip(),
            raw_level=(data.get("Level") or "").strip(),
            original_tags=list(raw_tags),
            tags=list(raw_tags),
            extra={
                "source_format": self.name,
                "source_row": data,
                "call": data["Call"],
                "response": data["Response"],
            },
        )
