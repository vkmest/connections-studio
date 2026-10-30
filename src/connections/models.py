"""Puzzle invariants shared by the API, desktop and terminal."""

from collections import Counter
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def normalize_words(words: list[str]) -> list[str]:
    return [" ".join(word.split()).upper() for word in words]


def validate_words(words: list[str], count: int) -> list[str]:
    normalized = normalize_words(words)
    if len(normalized) != count:
        raise ValueError(f"Expected exactly {count} words; found {len(normalized)}.")
    if any(not word or len(word) > 80 for word in normalized):
        raise ValueError("Each tile needs a word or phrase between 1 and 80 characters.")
    if len(set(normalized)) != count:
        raise ValueError("Every tile must be unique. Check for duplicate words.")
    return normalized


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Group(StrictModel):
    title: str = Field(min_length=1, max_length=100)
    words: list[str] = Field(min_length=4, max_length=4)
    explanation: str = Field(min_length=1, max_length=500)
    confidence: Literal["high", "medium", "low"]

    @field_validator("title", "explanation")
    @classmethod
    def check_description(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Category titles and explanations cannot be blank.")
        return value

    @field_validator("words")
    @classmethod
    def check_words(cls, words: list[str]) -> list[str]:
        return validate_words(words, 4)


class SolveRequest(StrictModel):
    words: list[str]
    locked: list[Group] = Field(default_factory=list, max_length=4)
    rejected: list[list[str]] = Field(default_factory=list, max_length=32)
    mode: Literal["budget", "deeper", "extended"] = "budget"

    @field_validator("words")
    @classmethod
    def check_board(cls, words: list[str]) -> list[str]:
        return validate_words(words, 16)

    @field_validator("rejected")
    @classmethod
    def check_rejections(cls, groups: list[list[str]]) -> list[list[str]]:
        return [validate_words(words, 4) for words in groups]

    @model_validator(mode="after")
    def check_constraints(self):
        locked_words = [word for group in self.locked for word in group.words]
        if len(locked_words) != len(set(locked_words)):
            raise ValueError("Locked groups overlap.")
        if not set(locked_words).issubset(self.words):
            raise ValueError("A locked group contains a word outside this board.")
        for rejected in self.rejected:
            if not set(rejected).issubset(self.words):
                raise ValueError("A rejected group contains a word outside this board.")
            if any(set(rejected) == set(group.words) for group in self.locked):
                raise ValueError("A group cannot be both locked and rejected.")
        return self


class Solution(StrictModel):
    groups: list[Group] = Field(min_length=4, max_length=4)

    def validate_for(self, request: SolveRequest) -> None:
        actual = [word for group in self.groups for word in group.words]
        if Counter(actual) != Counter(request.words):
            raise ValueError("The answer must use each of the 16 words exactly once.")
        sets = [set(group.words) for group in self.groups]
        if any(set(group.words) not in sets for group in request.locked):
            raise ValueError("The answer changed a locked group.")
        if any(set(rejected) in sets for rejected in request.rejected):
            raise ValueError("The answer repeated a rejected group.")


class Extraction(StrictModel):
    # Variable length lets the model report an unreadable or partial board honestly.
    words: list[str] = Field(max_length=16)
    warning: str = Field(max_length=500)

    @field_validator("words")
    @classmethod
    def normalize(cls, words: list[str]) -> list[str]:
        normalized = normalize_words(words)
        if any(len(word) > 80 for word in normalized):
            raise ValueError("Extracted text is too long for a tile.")
        return normalized


class Usage(StrictModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0
    estimated_cost_usd: float | None = 0.0
