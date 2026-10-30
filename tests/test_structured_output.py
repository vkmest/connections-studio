import json

import pytest
from pydantic import Field, create_model

from connections.models import Extraction, Group, Solution, StrictModel
from connections.structured_output import (
    OutputFormatError,
    json_format_instructions,
    parse_json_answer,
)


@pytest.mark.parametrize(
    "schema",
    [
        Extraction,
        Solution,
        create_model(
            "RemainingTwo",
            __base__=StrictModel,
            groups=(list[Group], Field(min_length=2, max_length=2)),
        ),
    ],
)
def test_format_example_is_valid_for_the_requested_schema(schema):
    instructions = json_format_instructions(schema)
    start = instructions.index("\n{") + 1
    example, _ = json.JSONDecoder().raw_decode(instructions[start:])
    schema.model_validate(example)


def test_parser_never_extracts_an_answer_from_surrounding_prose():
    with pytest.raises(OutputFormatError, match="malformed JSON"):
        parse_json_answer(Extraction, 'Here is the answer: {"words": [], "warning": ""}')
