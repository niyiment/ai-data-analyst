"""Enforce file-length and Python function-length hard limits from docs/CODING_STANDARDS.md."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

MAX_FILE_LINES = 250
MAX_FUNCTION_LINES = 40
EXCLUDED_DIRS = {".venv", "node_modules", ".next", "__pycache__", ".git"}


def iter_source_files(root: Path, suffixes: set[str]) -> list[Path]:
    """Return all source files under root matching suffixes, skipping build/vendor dirs."""
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix in suffixes:
            files.append(path)
    return sorted(files)


def check_python_functions(path: Path, source: str) -> list[str]:
    """Check that every Python function/method is within MAX_FUNCTION_LINES."""
    violations: list[str] = []
    tree = ast.parse(source, filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = node.end_lineno or node.lineno
            length = end - node.lineno + 1
            if length > MAX_FUNCTION_LINES:
                violations.append(
                    f"{path}:{node.lineno}: function '{node.name}' is {length} lines "
                    f"(hard limit: {MAX_FUNCTION_LINES})"
                )
    return violations


def check_repo(repo_root: Path) -> list[str]:
    """Run file-length and function-length checks across api/src, web/src, and scripts."""
    violations: list[str] = []
    roots = [repo_root / "api" / "src", repo_root / "web" / "src", repo_root / "scripts"]
    for scan_root in roots:
        if not scan_root.exists():
            continue
        for path in iter_source_files(scan_root, {".py", ".ts", ".tsx"}):
            source = path.read_text(encoding="utf-8")
            line_count = len(source.splitlines())
            if line_count > MAX_FILE_LINES:
                violations.append(
                    f"{path}: file is {line_count} lines (hard limit: {MAX_FILE_LINES})"
                )
            if path.suffix == ".py":
                violations.extend(check_python_functions(path, source))
    return violations


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    violations = check_repo(repo_root)
    if violations:
        for item in violations:
            print(f"LIMIT VIOLATION: {item}")
        return 1
    print("Size and function-length checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
