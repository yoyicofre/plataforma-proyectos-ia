.PHONY: install dev lint test run preflight scaffold

install:
	python -m pip install -U pip
	pip install -e ".[dev]"

dev:
	uvicorn src.main:app --reload

lint:
	ruff check .

test:
	pytest

run:
	uvicorn src.main:app --host 0.0.0.0 --port 8000

preflight:
	python scripts/preflight_check.py

scaffold:
	python scripts/scaffold_from_spec.py specs/project.spec.yml
