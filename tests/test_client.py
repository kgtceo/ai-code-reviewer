"""LLMClient.structured — the validation-retry path, offline.

Regression for a live 400 from the API: when the first tool call failed schema
validation, the retry appended the assistant `tool_use` turn followed by a plain-text
user message. The API requires a `tool_result` block answering that `tool_use`, so
every retry was rejected and the error surfaced as BadRequestError instead of a
corrected second attempt.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ai_code_reviewer.client import LLMClient, StructuredCallError
from ai_code_reviewer.config import Settings
from ai_code_reviewer.models import Review


def _tool_use(tool_id: str, name: str, payload: dict) -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=tool_id, name=name, input=payload)


class FakeAnthropic:
    """Returns scripted responses in order and records every request's messages."""

    def __init__(self, responses: list[list[SimpleNamespace]]) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(content=self._responses.pop(0))


# `line` is not an int and the other Finding fields are missing → ValidationError.
INVALID = {"summary": "x", "findings": [{"file": "a.py", "line": "seven"}]}
VALID = {"summary": "Safe to merge.", "findings": []}


def _settings(retries: int = 2) -> Settings:
    return Settings(anthropic_api_key="test", max_schema_retries=retries)


def test_retry_answers_tool_use_with_tool_result_and_returns_valid_second_attempt():
    fake = FakeAnthropic(
        [
            [_tool_use("toolu_1", "emit_review", INVALID)],
            [_tool_use("toolu_2", "emit_review", VALID)],
        ]
    )
    result = LLMClient(_settings(), anthropic=fake).structured(
        schema=Review, system="sys", user="review this"
    )

    assert result.summary == "Safe to merge."
    assert len(fake.calls) == 2

    retry_messages = fake.calls[1]["messages"]
    assert [m["role"] for m in retry_messages] == ["user", "assistant", "user"]
    # The assistant turn is echoed back verbatim so the tool_use id is present...
    assert retry_messages[1]["content"][0].id == "toolu_1"
    # ...and answered by a tool_result block that carries the validation error.
    answer = retry_messages[2]["content"][0]
    assert answer["type"] == "tool_result"
    assert answer["tool_use_id"] == "toolu_1"
    assert answer["is_error"] is True
    assert "failed validation" in answer["content"]
    assert "line" in answer["content"]  # the offending field is named for the model


def test_gives_up_after_configured_retries():
    fake = FakeAnthropic(
        [
            [_tool_use("toolu_1", "emit_review", INVALID)],
            [_tool_use("toolu_2", "emit_review", INVALID)],
        ]
    )
    with pytest.raises(StructuredCallError):
        LLMClient(_settings(retries=1), anthropic=fake).structured(
            schema=Review, system="sys", user="review this"
        )
    assert len(fake.calls) == 2  # initial attempt + one retry, then stop


def test_valid_first_attempt_makes_one_call():
    fake = FakeAnthropic([[_tool_use("toolu_1", "emit_review", VALID)]])
    LLMClient(_settings(), anthropic=fake).structured(schema=Review, system="sys", user="u")
    assert len(fake.calls) == 1
    assert fake.calls[0]["tool_choice"] == {"type": "tool", "name": "emit_review"}
