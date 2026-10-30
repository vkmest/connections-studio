"""Concrete JSON examples and conservative parsing for JSON-mode providers."""

import json
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from connections.models import Extraction

T = TypeVar("T", bound=BaseModel)


class OutputFormatError(ValueError):
    pass


def json_format_instructions(schema: type[BaseModel]) -> str:
    definition = schema.model_json_schema()
    if schema is Extraction:
        example = {"words": [f"EXAMPLE_WORD_{i:02}" for i in range(1, 17)], "warning": ""}
    else:
        count = definition["properties"]["groups"]["minItems"]
        example = {
            "groups": [
                {
                    "title": f"Category {index + 1}",
                    "words": [f"EXAMPLE_WORD_{index * 4 + offset + 1:02}" for offset in range(4)],
                    "explanation": "A brief explanation of the shared connection.",
                    "confidence": "medium",
                }
                for index in range(count)
            ]
        }
    return (
        "\nReturn one JSON object only, without Markdown or surrounding commentary. "
        "Include every required field, using exactly the field names shown.\n"
        "Example JSON (format only; NEVER copy these example words or categories):\n"
        + json.dumps(example)
        + "\nRequired JSON schema:\n"
        + json.dumps(definition)
    )


def parse_json_answer(schema: type[T], content: str | None) -> T:
    raw = (content or "").strip()
    if not raw:
        raise OutputFormatError(
            "The provider returned a blank final answer. JSON mode can produce an empty "
            "or whitespace-only response even when marked finished."
        )
    # Unwrap only a whole fenced document; don't guess at JSON inside prose or reasoning.
    lines = raw.splitlines()
    if (
        len(lines) >= 3
        and lines[0].strip().lower() in {"```json", "```"}
        and lines[-1].strip() == "```"
    ):
        raw = "\n".join(lines[1:-1])
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise OutputFormatError(
            "The provider returned malformed JSON instead of a complete answer."
        ) from None
    try:
        return schema.model_validate(data)
    except ValidationError:
        if schema is Extraction:
            expected = "Expected a words array and warning text."
        else:
            count = schema.model_json_schema()["properties"]["groups"]["minItems"]
            expected = (
                f"Expected {count} groups of four words, each with title, words, explanation "
                "and confidence (high, medium or low)."
            )
        raise OutputFormatError(
            "The provider's JSON was readable, but its fields, types or counts did not match "
            "the required answer format. " + expected
        ) from None
