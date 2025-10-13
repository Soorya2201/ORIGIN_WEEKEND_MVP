.PHONY: dev test cov fmt lint up down livecheck test-full

dev:
	uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000

test:
	pytest -q

cov:
	pytest --cov=app --cov-report=term-missing

fmt:
	black .
	isort .

lint:
	ruff check .

up:
	docker compose up -d postgres redis

down:
	docker compose down

livecheck:
	python -c "from app.insights.clients import ensure_live; ensure_live(); print('Gemini OK')"

test-full:
	python run_full_test.py
