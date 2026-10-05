.PHONY: up down logs backend frontend test lint seed

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

backend:
	cd backend && . .venv/bin/activate && alembic upgrade head && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && . .venv/bin/activate && pytest -q

lint:
	cd backend && . .venv/bin/activate && ruff check . && ruff format --check . && mypy app
	cd frontend && npm run lint

seed:
	cd backend && . .venv/bin/activate && python scripts_seed.py
