# Engineering Standards

## Convenciones
- estructura por módulos (bounded context)
- routers: FastAPI `APIRouter`
- services: lógica de negocio
- schemas: Pydantic
- dependencies: auth/DI por módulo

## Calidad (mínimo)
- Lint: `ruff check .`
- Tests: `pytest`
- Bugfix => test de regresión obligatorio

## PR
- descripción + AC
- tests
- docs

## Errores
- usar helpers de `src/core/errors.py`
