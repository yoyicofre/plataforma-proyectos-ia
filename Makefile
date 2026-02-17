.PHONY: install dev lint test run preflight scaffold lambda-package-layer lambda-package lambda-deploy frontend-publish backend-deploy-full full-release

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

lambda-package-layer:
	powershell -ExecutionPolicy Bypass -File scripts/package_lambda_layer.ps1

lambda-package:
	powershell -ExecutionPolicy Bypass -File scripts/package_lambda.ps1

lambda-deploy: lambda-package-layer lambda-package
	powershell -ExecutionPolicy Bypass -File scripts/deploy_lambda.ps1

frontend-publish:
	powershell -ExecutionPolicy Bypass -File scripts/deploy_frontend_git.ps1

backend-deploy-full:
	powershell -ExecutionPolicy Bypass -File scripts/deploy_backend_full.ps1

full-release:
	powershell -ExecutionPolicy Bypass -File scripts/release_full.ps1
