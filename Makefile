.PHONY: test run seed compose-up compose-down

test:
	cd backend && pytest -q

run:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

seed:
	cd backend && python -m app.seed

compose-up:
	docker compose up --build

compose-down:
	docker compose down -v
