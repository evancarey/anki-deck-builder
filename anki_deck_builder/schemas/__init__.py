from .french_call_response import FrenchCallResponseSchema
from .french_sentences import FrenchSentencesSchema


def available_schemas():
    return {
        FrenchSentencesSchema.name: FrenchSentencesSchema,
        FrenchCallResponseSchema.name: FrenchCallResponseSchema,
    }


def get_schema(name: str):
    schemas = available_schemas()
    if name not in schemas:
        raise ValueError(f"Unknown schema plugin: {name}")
    return schemas[name]()
