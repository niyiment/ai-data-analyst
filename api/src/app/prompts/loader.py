"""Prompt loader for versioned template files."""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "templates"


def load_prompt(name: str, version: str = "v1") -> str:
    """Load a versioned prompt template from disk."""
    path = PROMPTS_DIR / f"{name}_{version}.txt"
    if not path.is_file():
        raise FileNotFoundError(f"Prompt template not found: {path.name}")
    return path.read_text(encoding="utf-8")
