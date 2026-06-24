"""Harness tests — marker: test_harness."""

from __future__ import annotations

from pathlib import Path

from harness.chat import (
    chat,
    decline_message,
    is_legal_advice_query,
    load_system_prompt,
)


def test_system_prompt_loaded() -> None:
    text = load_system_prompt()
    assert "data_quality" in text
    assert "legal advice" in text.lower()


def test_legal_advice_declined() -> None:
    assert is_legal_advice_query("Should I appeal my court martial conviction?")
    result = chat("Should I sue the government for my case?")
    assert result["declined"] is True
    assert "legal advice" in result["reply"].lower()


def test_chat_with_mock_tool_use(fixture_db) -> None:
    def mock_create(system, user, tools):
        return {
            "tool_calls": [
                {"name": "get_entity", "arguments": {"entity_id": "aft"}},
            ],
            "text": "The Armed Forces Tribunal (aft) has the following structural profile:",
        }

    result = chat(
        "Tell me about the Armed Forces Tribunal",
        create_message=mock_create,
    )
    assert result["declined"] is False
    assert "get_entity" in result["tools_used"]
    assert "aft" in result["reply"]
    assert "data_quality" in result["reply"]


def test_harness_test_pairs_fixture_exists() -> None:
    path = Path(__file__).parent / "fixtures" / "harness_test_pairs.md"
    assert path.exists()
    text = path.read_text()
    assert "Pair 1" in text
    assert "legal advice" in text.lower()
