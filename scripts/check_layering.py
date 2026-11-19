"""Enforce architectural layering rules from docs/CODING_STANDARDS.md and ADR-0002."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

FEATURE_MODULES = {"sessions", "datasets", "query", "charts", "insights", "reports", "evaluation"}
FORBIDDEN_BACKEND_IMPORTS: dict[str, set[str]] = {
    "router": {"repository"},
    "repository": {"router", "service"},
}
TS_IMPORT_RE = re.compile(r"""from\s+["']([^"']+)["']""")


def extract_python_imports(path: Path) -> list[str]:
    """Return dotted module names imported by a Python file."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def check_backend_layering(api_src: Path) -> list[str]:
    """Verify router -> service -> repository one-way dependencies in api/src/app."""
    violations: list[str] = []
    app_dir = api_src / "app"
    for module in FEATURE_MODULES:
        mod_dir = app_dir / module
        if not mod_dir.exists():
            continue
        for layer, forbidden in FORBIDDEN_BACKEND_IMPORTS.items():
            file_path = mod_dir / f"{layer}.py"
            if not file_path.exists():
                continue
            for imported in extract_python_imports(file_path):
                parts = imported.split(".")
                if len(parts) >= 3 and parts[0] == "app" and parts[2] in forbidden:
                    violations.append(
                        f"{file_path}: {layer} must not import {imported}"
                    )
    return violations


def check_frontend_features(web_src: Path) -> list[str]:
    """Verify frontend features only import other features via their index.ts public surface."""
    violations: list[str] = []
    features_dir = web_src / "features"
    if not features_dir.exists():
        return violations
    for path in features_dir.rglob("*.ts*"):
        rel = path.relative_to(features_dir)
        own_feature = rel.parts[0]
        content = path.read_text(encoding="utf-8")
        for target in TS_IMPORT_RE.findall(content):
            if target.startswith("@/features/"):
                parts = target.removeprefix("@/features/").split("/")
                if len(parts) > 1 and parts[0] != own_feature:
                    violations.append(
                        f"{path}: cross-feature import '{target}' must use '@/features/{parts[0]}'"
                    )
    return violations


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    violations = check_backend_layering(repo_root / "api" / "src")
    violations.extend(check_frontend_features(repo_root / "web" / "src"))
    if violations:
        for item in violations:
            print(f"LAYERING VIOLATION: {item}")
        return 1
    print("Layering checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
