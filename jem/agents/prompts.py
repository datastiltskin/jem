"""Prompt loading — always from .claude/prompts/, never inline."""

from __future__ import annotations

from pathlib import Path

JEM_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = JEM_ROOT / ".claude" / "prompts"


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text()
