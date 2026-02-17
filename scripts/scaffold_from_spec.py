#!/usr/bin/env python3

"""Scaffold (Idea → Esqueleto) desde `project.spec.yml`.

Uso:
  python scripts/scaffold_from_spec.py specs/project.spec.yml

Safe-by-default:
- Crea módulos/archivos faltantes.
- No sobreescribe archivos existentes (a menos que uses --force).
- Actualiza `src/main.py` entre markers `agentops`.

También sincroniza:
- `docs/platform/capabilities.yml` (agrega módulos faltantes como stubs)
- `docs/00_intake/module-map.md` (lista de módulos dentro de markers)

Spec recomendado: `specs/project.spec.yml`
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any, Dict, List, Union

try:
    import yaml  # type: ignore
except Exception as e:  # pragma: no cover
    raise SystemExit("PyYAML is required. Add 'pyyaml' to dependencies.") from e


# -------------------------
# Markers
# -------------------------
ROUTER_IMPORTS_START = "# [agentops:routers-imports:start]"
ROUTER_IMPORTS_END = "# [agentops:routers-imports:end]"
ROUTER_INCLUDE_START = "# [agentops:routers-include:start]"
ROUTER_INCLUDE_END = "# [agentops:routers-include:end]"

MODULE_LIST_START = "<!-- [agentops:module-list:start] -->"
MODULE_LIST_END = "<!-- [agentops:module-list:end] -->"


SNAKE = re.compile(r"^[a-z][a-z0-9_]*$")


# -------------------------
# Helpers
# -------------------------

def load_spec(path: Path) -> Dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Spec must be a YAML mapping at root.")
    return data


def ensure_file(path: Path, content: str, force: bool = False) -> bool:
    """Write file if missing, or overwrite if force=True. Returns True if written."""
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def normalize_module_entry(entry: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    if isinstance(entry, str):
        name = entry.strip()
        return {"name": name, "prefix": f"/{name}", "tags": [name], "description": ""}
    if isinstance(entry, dict) and "name" in entry:
        e = dict(entry)
        e["name"] = str(e["name"]).strip()
        e.setdefault("prefix", f"/{e['name']}")
        e.setdefault("tags", [e["name"]])
        e.setdefault("description", "")
        return e
    raise ValueError(f"Invalid module entry: {entry!r}")


def validate_modules(modules: List[Dict[str, Any]]) -> None:
    names = [m["name"] for m in modules]
    for n in names:
        if not n or not SNAKE.match(n):
            raise ValueError(f"Module name must be snake_case: {n!r}")
    if len(set(names)) != len(names):
        raise ValueError(f"Module names must be unique: {names}")


def replace_block(src: str, start: str, end: str, lines: List[str]) -> str:
    pattern = re.compile(re.escape(start) + r"(.*?)" + re.escape(end), re.S)
    m = pattern.search(src)
    if not m:
        raise ValueError(f"Marker block not found: {start}..{end}")
    inner = "\n".join(lines)
    return src[: m.start()] + start + "\n" + inner + "\n" + end + src[m.end() :]


# -------------------------
# Updaters
# -------------------------

def update_main_py(main_py: Path, modules: List[Dict[str, Any]]) -> None:
    text = main_py.read_text(encoding="utf-8")
    for marker in (ROUTER_IMPORTS_START, ROUTER_IMPORTS_END, ROUTER_INCLUDE_START, ROUTER_INCLUDE_END):
        if marker not in text:
            raise ValueError(f"main.py missing marker: {marker}")

    # Ensure health + users are always present (base del template)
    def ensure(mods: List[Dict[str, Any]], name: str, prefix: str, tags: List[str]) -> List[Dict[str, Any]]:
        if any(m["name"] == name for m in mods):
            return mods
        return [{"name": name, "prefix": prefix, "tags": tags, "description": ""}] + mods

    # Dedup (preserve order)
    seen = set()
    ordered: List[Dict[str, Any]] = []
    for m in modules:
        n = m["name"]
        if n not in seen:
            seen.add(n)
            ordered.append(m)
    modules = ordered

    modules = ensure(modules, "health", "", ["health"])
    modules = ensure(modules, "users", "/users", ["users"])

    new_import_lines: List[str] = []
    new_include_lines: List[str] = []

    for m in modules:
        name = m["name"]
        router_var = f"{name}_router"
        new_import_lines.append(f"from src.modules.{name}.router import router as {router_var}")

        if name == "health":
            new_include_lines.append(f"app.include_router({router_var})")
        else:
            prefix = m.get("prefix") or f"/{name}"
            tags = m.get("tags") or [name]
            new_include_lines.append(f'app.include_router({router_var}, prefix="{prefix}", tags={tags})')

    updated = replace_block(text, ROUTER_IMPORTS_START, ROUTER_IMPORTS_END, new_import_lines)
    updated = replace_block(updated, ROUTER_INCLUDE_START, ROUTER_INCLUDE_END, ["    " + l for l in new_include_lines])

    if updated != text:
        main_py.write_text(updated, encoding="utf-8")


def update_module_map(module_map_md: Path, modules: List[Dict[str, Any]]) -> None:
    if not module_map_md.exists():
        return
    text = module_map_md.read_text(encoding="utf-8")
    if MODULE_LIST_START not in text or MODULE_LIST_END not in text:
        # No markers: do not touch.
        return
    lines = [f"- {m['name']} ({m.get('prefix') or '/' + m['name']})" for m in modules]
    updated = replace_block(text, MODULE_LIST_START, MODULE_LIST_END, lines)
    if updated != text:
        module_map_md.write_text(updated, encoding="utf-8")


def update_capabilities(capabilities_yml: Path, modules: List[Dict[str, Any]]) -> None:
    data: Dict[str, Any]
    if capabilities_yml.exists():
        parsed = yaml.safe_load(capabilities_yml.read_text(encoding="utf-8"))
        data = parsed if isinstance(parsed, dict) else {}
    else:
        data = {}

    mods = data.get("modules")
    if not isinstance(mods, list):
        mods = []
        data["modules"] = mods

    existing = {m.get("name") for m in mods if isinstance(m, dict)}

    for m in modules:
        name = m["name"]
        if name in existing:
            continue
        mods.append(
            {
                "name": name,
                "owner": "TBD",
                "capabilities": [],
            }
        )

    # Preserve a readable dump
    out = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    capabilities_yml.write_text(out, encoding="utf-8")


# -------------------------
# Scaffolding
# -------------------------

def scaffold_module(root: Path, module: Dict[str, Any], force: bool = False) -> None:
    name = module["name"]
    mod_dir = root / "src" / "modules" / name
    mod_dir.mkdir(parents=True, exist_ok=True)
    ensure_file(mod_dir / "__init__.py", "", force=force)

    # Router: por defecto exige usuario (AuthZ por módulo se decide luego)
    router_py = f"""from fastapi import APIRouter, Depends\nfrom src.core.security import User\nfrom src.modules.{name}.dependencies import current_user\n\nrouter = APIRouter()\n\n\n@router.get(\"/\")\ndef index(user: User = Depends(current_user)) -> dict:\n    return {{\"module\": \"{name}\", \"user\": user.id}}\n\n"""
    ensure_file(mod_dir / "router.py", router_py, force=force)

    # Schemas
    cls_name = "".join([p.capitalize() for p in name.split("_")])
    schemas_py = f"""from pydantic import BaseModel\n\n\nclass {cls_name}Item(BaseModel):\n    id: str\n    # TODO: agrega campos reales\n\n"""
    ensure_file(mod_dir / "schemas.py", schemas_py, force=force)

    # Service
    service_py = f"""# Servicio / lógica de negocio para el módulo {name}\n# TODO: implementar reglas de negocio\n\n"""
    ensure_file(mod_dir / "service.py", service_py, force=force)

    # Dependencies
    dependencies_py = """from fastapi import Depends\nfrom src.core.security import User, get_current_user\n\n\ndef current_user(user: User = Depends(get_current_user)) -> User:\n    return user\n\n"""
    ensure_file(mod_dir / "dependencies.py", dependencies_py, force=force)

    # Docs
    docs_mod = root / "docs" / "modules" / name
    docs_mod.mkdir(parents=True, exist_ok=True)

    readme = f"""# Módulo: {name}\n\n## Propósito\n{(module.get('description') or '').strip() or 'TODO: describir el propósito del módulo.'}\n\n## Endpoints\n- `{module.get('prefix') or f'/{name}'}`\n\n## Datos\n- Entidades principales: TODO\n\n## Permisos\n- Roles permitidos: TODO\n\n## Observabilidad\n- Logs/metrics relevantes: TODO\n"""
    ensure_file(docs_mod / "README.md", readme, force=force)

    changelog = """# Changelog\n\n## Unreleased\n- ...\n"""
    ensure_file(docs_mod / "CHANGELOG.md", changelog, force=force)

    # Test skeleton
    tests_dir = root / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    test_py = f"""from fastapi.testclient import TestClient\n\nfrom src.main import create_app\n\n\ndef test_{name}_smoke() -> None:\n    app = create_app()\n    client = TestClient(app)\n    # TODO: ajusta si tu módulo requiere auth real\n    resp = client.get(\"{module.get('prefix') or f'/{name}'}/\")\n    # Puede ser 200 o 403 dependiendo de tu capa de auth; deja el contrato explícito aquí.
    assert resp.status_code in (200, 403)\n"""
    ensure_file(tests_dir / f"test_{name}.py", test_py, force=force)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=str, help="Path a specs/project.spec.yml")
    parser.add_argument("--force", action="store_true", help="Sobrescribe archivos existentes")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    spec_path = (root / args.spec).resolve() if not Path(args.spec).is_absolute() else Path(args.spec)
    spec = load_spec(spec_path)

    modules_raw = spec.get("modules", [])
    if not isinstance(modules_raw, list):
        raise ValueError("'modules' must be a list")

    modules = [normalize_module_entry(e) for e in modules_raw]
    validate_modules(modules)

    for m in modules:
        scaffold_module(root, m, force=args.force)

    update_main_py(root / "src" / "main.py", modules)
    update_module_map(root / "docs" / "00_intake" / "module-map.md", modules)
    update_capabilities(root / "docs" / "platform" / "capabilities.yml", modules)

    print(f"Scaffold complete: {len(modules)} module(s) processed.")


if __name__ == "__main__":
    main()
