# Zomato-like Food Delivery App

A complete end-to-end starter for a food delivery system with backend APIs, database schema, role-based auth, cart, checkout, order lifecycle, delivery assignment, outbox worker, Docker Compose, React UI, and automated tests.

This is **not** a full Zomato production system, but it is structured like a scalable production starter that you can extend into microservices.

## Tech stack

- Backend: FastAPI, SQLAlchemy 2.x, Pydantic v2, JWT auth
- Database: SQLite for local tests; PostgreSQL in Docker/production
- Cache/infra: Redis container included; in-process cache adapter for local starter
- Worker: transactional outbox processor for async events
- Frontend: React + Vite + TypeScript
- Tests: pytest + FastAPI TestClient
- Observability: request IDs, `/metrics`, health checks

## Core features

- Register/login users
- Roles: customer, restaurant owner, delivery partner, admin
- Create restaurants and menu items
- Search restaurants with pagination and cache-friendly query shape
- Customer cart with single-restaurant constraint
- Checkout with `X-Idempotency-Key` to make retries safe
- Order lifecycle: placed → accepted → preparing → out for delivery → delivered
- Cancel/refund path for valid transitions
- Delivery partner assignment
- Outbox events for order placed/status changed/delivery assigned
- Health checks and Prometheus-compatible metrics endpoint

## Run locally without Docker

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload
```

Open:

- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/v1/health/ready`
- Metrics: `http://localhost:8000/metrics`

Demo users created by `python -m app.seed`:

| Email | Role | Password |
|---|---|---|
| owner@example.com | Restaurant owner | Password123 |
| customer@example.com | Customer | Password123 |
| partner@example.com | Delivery partner | Password123 |
| admin@example.com | Admin | Password123 |

## Run with Docker Compose

```bash
docker compose up --build
```

Services:

- API: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- Postgres: `localhost:5432`
- Redis: `localhost:6379`

To seed Docker Postgres after the API container starts:

```bash
docker compose exec api python -m app.seed
```

## Run tests

```bash
cd backend
pytest -q
```

Current suite covers auth, role security, restaurant/menu operations, cart rules, idempotent checkout, order status transitions, delivery assignment, and health checks.

## Example API flow

```bash
# 1. Register a customer
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"newcustomer@example.com","password":"Password123","full_name":"New Customer","role":"CUSTOMER"}'

# 2. Login and copy access_token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"customer@example.com","password":"Password123"}'

# 3. List restaurants
curl http://localhost:8000/api/v1/restaurants

# 4. Add menu item to cart
curl -X POST http://localhost:8000/api/v1/cart/items \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"menu_item_id":"MENU_ITEM_ID","quantity":2}'

# 5. Checkout safely with idempotency key
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H 'X-Idempotency-Key: checkout-unique-001' \
  -H 'Content-Type: application/json' \
  -d '{"delivery_address":"221B Baker Street, Bengaluru","payment_method":"UPI"}'
```

## Project layout

```text
backend/
  app/
    api/              # FastAPI routes and dependencies
    core/             # config, database, security, middleware, metrics
    models/           # SQLAlchemy ORM schema
    schemas/          # Pydantic request/response DTOs
    services/         # business logic
    seed.py           # demo data
    worker.py         # transactional outbox worker
  tests/              # automated tests
frontend/
  src/                # React UI
docs/
  architecture.md     # non-functional requirements and production roadmap
load-tests/
  k6_smoke.js         # simple load smoke script
```

## Production notes

For serious Zomato-scale production, split the bounded contexts into services: catalog/search, cart, order, payment, delivery, notification, identity, reviews, and promotions. Keep the idempotency/outbox patterns, add Kafka or another durable broker, use Redis cluster, Postgres read replicas or sharded databases, object storage/CDN for images, and a search/geo index such as OpenSearch/PostGIS.
