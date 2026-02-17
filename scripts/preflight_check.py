#!/usr/bin/env python3

"""Preflight (DoR) check.

Propósito:
- Bloquear el inicio de implementación si falta lo básico.

Uso:
  python scripts/preflight_check.py

Qué valida (mínimo):
- Artefactos DoR existen
- project.spec.yml tiene `project.name`, `project.slug` y módulos
- nombres de módulos únicos + snake_case

Nota:
Este script **no** intenta validar la calidad del contenido (eso lo hace el proceso
PROJECT-FACTORY + review humana). Es un gate mecánico.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml  # type: ignore
except Exception as e:
    raise SystemExit("PyYAML is required. Install dependencies: pip install -e '.[dev]'") from e


SNAKE = re.compile(r"^[a-z][a-z0-9_]*$")

REQUIRED_FILES = [
    "docs/00_intake/project-brief.md",
    "docs/00_intake/PRD.md",
    "docs/00_intake/AC.md",
    "docs/00_intake/NFR.md",
    "docs/00_intake/out-of-scope.md",
    "docs/00_intake/risk-register.md",
    "docs/00_intake/module-map.md",
    "docs/platform/capabilities.yml",
    "docs/security/permission-matrix.md",
    "specs/project.spec.yml",
]


def die(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def load_yaml(path: Path) -> Dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        die(f"YAML root must be a mapping: {path}")
    return data


def validate_spec(spec: Dict[str, Any]) -> None:
    project = spec.get("project")
    if not isinstance(project, dict):
        die("spec: missing 'project' mapping")

    name = str(project.get("name") or "").strip()
    slug = str(project.get("slug") or "").strip()
    if not name:
        die("spec: project.name is required")
    if not slug or not SNAKE.match(slug):
        die("spec: project.slug is required and must be snake_case (e.g., fleet_control)")

    modules_raw = spec.get("modules")
    if not isinstance(modules_raw, list) or len(modules_raw) == 0:
        die("spec: 'modules' must be a non-empty list")

    names: List[str] = []
    for entry in modules_raw:
        if isinstance(entry, str):
            mod = entry.strip()
        elif isinstance(entry, dict) and "name" in entry:
            mod = str(entry.get("name") or "").strip()
        else:
            die(f"spec: invalid module entry: {entry!r}")

        if not mod or not SNAKE.match(mod):
            die(f"spec: module name must be snake_case: {mod!r}")
        names.append(mod)

    if len(set(names)) != len(names):
        die(f"spec: module names must be unique (found duplicates): {names}")


def main() -> None:
    root = Path(__file__).resolve().parents[1]

    missing = [p for p in REQUIRED_FILES if not (root / p).exists()]
    if missing:
        die("Preflight failed. Missing required files:\n- " + "\n- ".join(missing))

    spec = load_yaml(root / "specs/project.spec.yml")
    validate_spec(spec)

    print("Preflight OK: DoR artifacts present and project.spec.yml is valid.")


if __name__ == "__main__":
    main()
