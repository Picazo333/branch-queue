"""Design note, bilingual run instructions, and the stdlib-only boundary."""

import ast
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ALLOWED_IMPORTS = {
    "__future__",
    "argparse",
    "collections",
    "dataclasses",
    "datetime",
    "sys",
}


def test_design_note_explains_efficiency_and_concurrent_mutation_order():
    text = (ROOT / "DESIGN.md").read_text(encoding="utf-8")
    lowered = text.lower()
    assert "O(1)" in text
    assert "O(n)" in text
    assert "popleft" in text
    assert "lista compartida" in lowered
    assert "shared list" in lowered
    assert "dos agentes" in lowered
    assert "two agents" in lowered
    assert "La primera mutación de estado es el retiro de la cabeza" in text
    assert "The first state mutation is the removal of that queue's head" in text


def test_application_imports_are_stdlib_only():
    source = (ROOT / "branch_queue.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    assert modules <= ALLOWED_IMPORTS
    assert {"collections", "datetime"} <= modules
    assert "pytest" not in source
    assert "deque" in source


def test_project_declares_no_runtime_dependencies():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["dependencies"] == []


def test_readme_has_bilingual_exact_commands():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "## Español" in text
    assert "## English" in text
    assert "python3 branch_queue.py" in text
    assert "python3 branch_queue.py --lang en" in text
    assert "python3 -m pip install pytest" in text
    assert "python3 -m pytest -q" in text
