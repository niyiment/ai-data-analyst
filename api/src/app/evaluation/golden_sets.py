"""Built-in golden question sets for evaluation (docs/TESTING.md 9.2).

Each set lives in golden/<name>.json and is validated against GoldenSet on load.
Reference SQL runs against the persistent demo_<name> schema created by migration.
"""

from pathlib import Path

from app.evaluation.schemas import GoldenSet

_GOLDEN_DIR = Path(__file__).parent / "golden"


def load_golden_sets(directory: Path = _GOLDEN_DIR) -> dict[str, GoldenSet]:
    """Load and validate every golden set JSON file in directory, keyed by set name."""
    sets = [
        GoldenSet.model_validate_json(path.read_text(encoding="utf-8"))
        for path in sorted(directory.glob("*.json"))
    ]
    return {s.name: s for s in sets}


GOLDEN_SETS: dict[str, GoldenSet] = load_golden_sets()
