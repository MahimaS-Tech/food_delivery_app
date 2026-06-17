# Architecture and Non-Functional Requirements

## High-level design

This repository is a modular monolith that can later be split into services. The current modules map to natural bounded contexts:

- Identity and access: users, JWT, role authorization
- Restaurant catalog: restaurants, menus, availability, city/cuisine filters
- Cart: single-restaurant active cart per customer
- Order: checkout, idempotency, payment status, order lifecycle
- Delivery: delivery partner assignment
- Events: transactional outbox for reliable async publishing

## Why this design supports scale

### Stateless API layer

The API keeps no sticky user session. JWT is sent on every request, so API containers can be horizontally scaled behind a load balancer.

### Database indexing

The schema includes indexes for common read paths:

- restaurant city/cuisine/status search
- menu availability per restaurant
- customer/status order history
- restaurant/status order dashboard
- delivery partner active orders
- idempotent checkout lookup

### Idempotent checkout

`POST /api/v1/orders` requires `X-Idempotency-Key`. If a client times out and retries the same checkout, the same order is returned instead of creating duplicates.

### Transactional outbox

Order creation/status changes and delivery assignment insert an outbox row in the same database transaction. A worker publishes the event later. This avoids the common failure where the database commit succeeds but the event publish fails.

### Cache-ready catalog

Restaurant search is isolated behind a cache adapter. The local implementation is in-process TTL cache; production should replace it with Redis cluster and add cache invalidation through events.

### Observability

Each request receives `X-Request-ID`. The app exposes Prometheus-compatible metrics at `/metrics` and liveness/readiness endpoints at `/api/v1/health/live` and `/api/v1/health/ready`.

## Zomato-like NFR checklist

| Requirement | Implementation in this starter | Production upgrade |
|---|---|---|
| High scalability | Stateless API, Docker services, indexed tables, pagination | Kubernetes HPA, service split, read replicas, sharding |
| Fault tolerance | Health checks, idempotency, outbox worker, DB connection pre-ping | Multi-AZ DB, broker retries/DLQ, circuit breakers, backup/restore drills |
| Low latency | Indexed search, cached catalog, compact DTOs | Redis cluster, CDN, OpenSearch/PostGIS, edge caching, p95 SLOs |
| Consistency | DB transactions around checkout | Saga orchestration for payment/order/delivery across services |
| Security | Password hashing, JWT, role-based access | OIDC, WAF, rate limiting, secret manager, audit logs |
| Observability | Request IDs, metrics endpoint | Central logs, distributed tracing, alerting, dashboards |
| Operability | Docker Compose, tests, health checks | Kubernetes manifests, blue/green deploys, canary releases |

## Recommended microservice split

When traffic grows, split in this order:

1. Catalog/search service: restaurant/menu browsing is read-heavy.
2. Order service: order lifecycle and idempotent checkout need strong ownership.
3. Payment service: isolate PCI/payment provider integration.
4. Delivery service: partner assignment, live location, ETA.
5. Notification service: SMS, email, push, WhatsApp.
6. Review/rating service: eventually consistent ratings.
7. Promotion/pricing service: coupons, surge fees, loyalty.

## Data model extension ideas

- Use PostGIS for nearby restaurant search.
- Add menu item images stored in object storage and served via CDN.
- Add inventory windows and restaurant operating hours.
- Add offer/coupon tables with rule evaluation.
- Add wallet/refund ledger instead of a single payment status column.
- Add reviews and rating aggregation jobs.
- Add delivery location events and WebSocket/SSE tracking.

## Reliability scenarios

### Client retries checkout after timeout

The API looks up `(customer_id, idempotency_key)` and returns the existing order. This prevents duplicate orders and duplicate payment authorization.

### Event broker is down

Order creation still commits to the database with an outbox event. The worker retries publishing later. In production, failed rows should go to a dead-letter queue after a retry limit.

### Restaurant menu changes while user checks out

Checkout revalidates menu availability and prices from the database, then snapshots item names and prices into `order_items` for historical correctness.

### API instance dies mid-request

Either the database transaction commits or it rolls back. Idempotency allows the client to retry safely.
