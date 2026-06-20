# E-Commerce Python Microservice — Architecture & Specification

---

## 1. System Overview

A backend-only, Python-based e-commerce microservice platform built for small-to-medium workloads. Designed to run on constrained hardware (8 GB RAM, Intel i3 4-core, 1 TB HDD). Every service follows the same structural contract enforced through two shared modules: `core-common` and `msg-common`.

**Design principles:**
- Every domain service extends `core-common` — no reimplementing CRUD, pagination, grids, or middleware
- Every event-driven integration goes through `msg-common` — no reimplementing producers, consumers, or routing
- One database per service (DB isolation)
- Event-driven communication between services via RabbitMQ
- Saga orchestration via Temporal (event/signal driven, no polling)
- Consul for service discovery and health registration

---

## 2. Hardware Budget & Service RAM Allocation

| Component | Estimated RAM |
|---|---|
| RabbitMQ | ~150–200 MB |
| Temporal server | ~300–400 MB |
| Consul | ~50–80 MB |
| PostgreSQL (shared instance, multiple DBs) | ~300–400 MB |
| Redis | ~50–100 MB |
| API Gateway (Traefik) | ~50 MB |
| 5 domain services (FastAPI + Uvicorn) | ~80–120 MB each (~500 MB total) |
| Workflow service (Temporal worker) | ~100 MB |
| Prometheus + Grafana (optional, dev only) | ~200–300 MB |
| **Total estimated** | **~1.8–2.2 GB active** |

Remaining headroom (~5–6 GB) covers OS, Docker overhead, HDD swap, and future services. Safe to run everything on Docker Compose locally and graduate to K8s later.

---

## 3. Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Language | Python 3.12+ | Async support, type hints, ecosystem |
| Web framework | FastAPI | Async, Pydantic-native, OpenAPI built-in |
| ASGI server | Uvicorn + Gunicorn | Production-grade, multi-worker |
| Data validation | Pydantic v2 | Fast, strict typing, used in core-common |
| ORM | SQLAlchemy 2.0 async | Async sessions, Alembic migrations |
| Migrations | Alembic | Per-service, base config in core-common |
| Database | PostgreSQL (one DB per service, shared instance) | ACID, relational |
| Cache / sessions | Redis | Lightweight, fast |
| Message broker | **RabbitMQ** | Low RAM, AMQP, routing keys, dead-letter queues |
| Workflow / Saga | **Temporal** | Durable, event/signal driven, no polling, Python SDK |
| Service discovery | Consul | Health checks, KV store, DNS |
| API Gateway | Traefik | Auto-discovers services via Consul tags |
| Auth | JWT (python-jose) + OAuth2 password flow | Standard, stateless |
| Logging | structlog | Structured JSON logs |
| Tracing | OpenTelemetry + Jaeger (optional) | Distributed trace context |
| Metrics | Prometheus + Grafana (optional, dev) | Per-service /metrics endpoint |
| Containerisation | Docker + Docker Compose | Local dev and staging |
| CI/CD | GitHub Actions | Lint, test, build, push |

---

## 4. Repository Structure

```
ecommerce-platform/
│
├── core-common/                  # Abstract base layer (pip package)
│   ├── core_common/
│   │   ├── controller/
│   │   │   └── base_controller.py
│   │   ├── service/
│   │   │   └── base_service.py
│   │   ├── repository/
│   │   │   └── base_repository.py
│   │   ├── domain/
│   │   │   └── base_domain.py
│   │   ├── schemas/
│   │   │   ├── base_schema.py
│   │   │   ├── grid_params.py
│   │   │   └── paged_response.py
│   │   ├── middleware/
│   │   │   ├── correlation_id.py
│   │   │   └── auth_middleware.py
│   │   ├── exceptions/
│   │   │   └── base_exception.py
│   │   ├── db/
│   │   │   └── session.py
│   │   └── health/
│   │       └── health_route.py
│   └── pyproject.toml
│
├── msg-common/                   # Messaging abstraction layer (pip package)
│   ├── msg_common/
│   │   ├── broker/
│   │   │   ├── base_producer.py
│   │   │   ├── base_consumer.py
│   │   │   └── connection.py
│   │   ├── router/
│   │   │   └── kafka_router.py   # named KafkaRouter but uses RabbitMQ internally
│   │   ├── middleware/
│   │   │   └── dlq_handler.py
│   │   ├── envelope/
│   │   │   └── event_envelope.py
│   │   └── retry/
│   │       └── retry_policy.py
│   └── pyproject.toml
│
├── service folders/
│   ├── user-service/
│   ├── product-service/
│   ├── order-service/
│   ├── payment-service/
│   ├── notification-service/
│   └── workflow-service/
│
├── docker-compose.yml
├── docker-compose.infra.yml       # RabbitMQ, Postgres, Redis, Consul, Temporal
└── .github/
    └── workflows/
        └── ci.yml
```

---

## 5. `core-common` Module — Detailed Spec

The `core-common` package is the abstract contract all services must follow. No domain service reimplements what lives here. Services only provide their own data and business logic; all structural behaviour is inherited.

### 5.1 `BaseController`

Wraps FastAPI `APIRouter`. Provides:
- Standard response envelope: `{ success, data, message, meta }`
- Grid, pagination, sorting, and filtering auto-wired from `GridParams`
- All routes return `PagedResponse` for list endpoints
- Exception handler integration built-in

Services only declare routes and call their own service layer. No response formatting logic in any domain service.

```
GridParams fields:
  page      int     default 1
  size      int     default 20, max 100
  sort_by   str     optional, field name
  order     enum    asc | desc
  filters   dict    optional key-value filter map
```

```
PagedResponse fields:
  items     List[T]
  total     int
  page      int
  size      int
  pages     int     total // size
```

### 5.2 `BaseService`

Provides:
- Generic `create`, `update`, `delete`, `get_by_id`, `list` with GridParams
- Pre/post hooks: `before_create`, `after_create`, `before_update`, `after_update`
- Domain services override hooks; they do not rewrite CRUD
- Validation delegation to `BaseSchema`
- Transaction management (unit of work pattern)

### 5.3 `BaseRepository`

Provides:
- SQLAlchemy 2.0 async session management
- Generic `find_by_id`, `find_all`, `save`, `delete`, `count`
- Dynamic filter builder from `GridParams.filters`
- Soft delete support via `deleted_at` column
- Domain repositories only add custom query methods

### 5.4 `BaseDomain` (entity base)

Pydantic v2 base model for all ORM-mapped entities:

```
Fields (auto-added to every entity):
  id          UUID      generated, primary key
  created_at  datetime  auto, UTC
  updated_at  datetime  auto on update, UTC
  deleted_at  datetime  nullable, soft delete
  is_active   bool      default True
```

### 5.5 `BaseSchema` (DTO base)

Three base schema types all domain schemas extend:
- `BaseRequestSchema` — input validation, strip unknown fields
- `BaseResponseSchema` — output model, camelCase alias generator
- `BaseUpdateSchema` — all fields optional, for PATCH

### 5.6 Grid & Pagination — How it works

Client sends query params: `?page=2&size=10&sort_by=created_at&order=desc&filters[status]=active`

`GridParams` parses these automatically in `BaseController`. Passed to `BaseService.list()` which passes to `BaseRepository.find_all()`. The repository builds the SQLAlchemy query dynamically. Returns `PagedResponse` from `BaseService`. The controller wraps it in the standard envelope. No domain service writes any of this logic.

### 5.7 Shared Middleware

- `CorrelationIdMiddleware` — generates or propagates `X-Correlation-ID` on every request, injects into structlog context
- `AuthMiddleware` — validates JWT, extracts user context, injects into request state
- `ExceptionHandler` — maps all `BaseException` subclasses to consistent HTTP error responses
- `HealthRoute` — `/health` and `/ready` endpoints auto-registered on every service

---

## 6. `msg-common` Module — Detailed Spec

Inspired by Apache Camel's context model. Services declare their message routes declaratively. No service writes RabbitMQ connection code, retry logic, or dead-letter handling.

### 6.1 `MessageRouter` (named KafkaRouter for API familiarity, RabbitMQ under the hood)

Route declaration DSL:

```python
from msg_common.router import MessageRouter

router = MessageRouter()

@router.consume(queue="order.created", exchange="orders")
async def handle_order_created(event: OrderCreatedEvent):
    await notification_service.send_order_confirmation(event)

@router.consume(queue="payment.failed", exchange="payments")
async def handle_payment_failed(event: PaymentFailedEvent):
    await order_service.cancel_order(event.order_id)
```

Services register the router on startup — no manual channel management.

### 6.2 `BaseProducer`

Provides:
- `publish(exchange, routing_key, event)` — wraps event in `EventEnvelope`, serialises, publishes
- Connection pooling via `aio-pika`
- Automatic reconnect with exponential backoff
- Correlation ID forwarded from request context

### 6.3 `BaseConsumer`

Provides:
- Auto-ack on success, nack on exception
- Configurable retry count before sending to DLQ
- Deserialisation and envelope unwrapping
- Injects correlation ID into structlog context per message

### 6.4 `EventEnvelope`

Every message published carries:

```
event_id         UUID      generated per publish
event_type       str       e.g. "order.created"
correlation_id   str       from request or generated
source_service   str       e.g. "order-service"
timestamp        datetime  UTC
version          str       "1.0"
payload          dict      actual event data
```

### 6.5 Dead-Letter Queue (DLQ) Strategy

Each exchange has a corresponding DLQ exchange. After N retries (configurable, default 3), the message goes to `{exchange}.dlq`. A separate DLQ consumer service (lightweight, part of `msg-common`) can inspect, replay, or alert on dead letters.

### 6.6 RabbitMQ Exchange / Queue Layout

```
Exchange: orders       Type: topic
  Queues:
    order.created         → notification-service, workflow-service
    order.cancelled       → notification-service, inventory-service

Exchange: payments     Type: topic
  Queues:
    payment.processed     → order-service, notification-service
    payment.failed        → order-service, workflow-service

Exchange: inventory    Type: topic
  Queues:
    inventory.reserved    → workflow-service
    inventory.released    → workflow-service

Exchange: notifications  Type: direct
  Queues:
    notification.send     → notification-service
```

---

## 7. Domain Services

Each service follows the same directory layout. Only the domain-specific files differ.

### Per-service directory layout

```
{service-name}/
├── app/
│   ├── main.py                   # FastAPI app factory, registers routers, middleware, consul
│   ├── controller/
│   │   └── {entity}_controller.py   # extends BaseController
│   ├── service/
│   │   └── {entity}_service.py      # extends BaseService
│   ├── repository/
│   │   └── {entity}_repository.py   # extends BaseRepository
│   ├── domain/
│   │   └── {entity}.py              # extends BaseDomain (SQLAlchemy model)
│   ├── schemas/
│   │   ├── request.py               # extends BaseRequestSchema
│   │   └── response.py              # extends BaseResponseSchema
│   ├── routes/
│   │   └── message_routes.py        # MessageRouter declarations (msg-common)
│   └── config.py                    # env vars, DB URL, RabbitMQ URL
├── migrations/                      # Alembic (base env from core-common)
├── tests/
├── Dockerfile
└── pyproject.toml
```

### 7.1 User Service

Responsibilities: registration, login, profile management, JWT issuance.

Entities: `User`, `UserAddress`

Endpoints (auto-paginated via core-common):
- `POST /auth/register`
- `POST /auth/login` → returns JWT
- `GET /users` → GridParams, PagedResponse
- `GET /users/{id}`
- `PATCH /users/{id}`
- `DELETE /users/{id}` → soft delete

Events published: `user.registered`, `user.deactivated`

Database: `users_db` (Postgres)

### 7.2 Product Service

Responsibilities: product catalogue, categories, inventory quantity.

Entities: `Product`, `Category`, `InventoryItem`

Endpoints:
- `GET /products` → grid, filter by category/price/status
- `GET /products/{id}`
- `POST /products`
- `PATCH /products/{id}`
- `DELETE /products/{id}`
- `GET /categories`

Events published: `inventory.reserved`, `inventory.released`, `inventory.updated`

Events consumed: none directly (Temporal calls this service's internal methods via activity)

Database: `products_db` (Postgres)

### 7.3 Order Service

Responsibilities: order lifecycle management.

Entities: `Order`, `OrderItem`, `OrderStatusHistory`

Order statuses: `PENDING → CONFIRMED → PROCESSING → SHIPPED → DELIVERED | CANCELLED | REFUNDED`

Endpoints:
- `POST /orders` → triggers Temporal `place-order` workflow
- `GET /orders` → grid, filter by status/user/date range
- `GET /orders/{id}`
- `PATCH /orders/{id}/cancel`

Events published: `order.created`, `order.confirmed`, `order.cancelled`

Events consumed: `payment.processed`, `payment.failed`

Database: `orders_db` (Postgres)

### 7.4 Payment Service

Responsibilities: payment processing, refunds, payment record management.

Entities: `Payment`, `Refund`

Payment statuses: `PENDING → SUCCESS | FAILED | REFUNDED`

Endpoints:
- `POST /payments` → called by Temporal activity (not directly by client)
- `GET /payments/{id}`
- `GET /payments/order/{order_id}`
- `POST /payments/{id}/refund`

Events published: `payment.processed`, `payment.failed`, `payment.refunded`

Database: `payments_db` (Postgres)

Note: In production, this service wraps an external payment gateway (Stripe, Razorpay). For dev/learning, a mock gateway is used.

### 7.5 Notification Service

Responsibilities: email, SMS, and in-app notification dispatch.

Entities: `NotificationLog`

Notification types: `EMAIL`, `SMS`, `PUSH`

Events consumed (all via msg-common MessageRouter):
- `order.created` → send order confirmation
- `order.cancelled` → send cancellation notice
- `payment.processed` → send payment receipt
- `payment.failed` → send payment failure alert
- `user.registered` → send welcome email

No REST endpoints exposed externally. Purely event-driven.

Database: `notifications_db` (Postgres) — for notification logs and delivery status

---

## 8. Workflow Service — Temporal Saga Spec

### 8.1 Why Temporal (event-driven, not polling)

Temporal uses **signals** and **activity completions** to drive workflow steps. The workflow worker sleeps between steps; it wakes only when an activity completes or a signal arrives. No busy polling. This fits the constrained hardware budget well.

### 8.2 Workflow: `place-order`

Triggered by: Order Service after `POST /orders`

```
Steps:
1. Activity: reserve_inventory(order_id, items)
      → calls Product Service internal API
      → on success: publish inventory.reserved
      → on fail: compensate → cancel order → end

2. Activity: process_payment(order_id, amount, user_id)
      → calls Payment Service internal API
      → on success: publish payment.processed
      → on fail: compensate → release_inventory → cancel order → end

3. Activity: confirm_order(order_id)
      → calls Order Service internal API
      → updates order status to CONFIRMED
      → publish order.confirmed

4. Activity: send_confirmation(order_id, user_id)
      → calls Notification Service internal API (or publishes event)
```

Compensation (Saga rollback) is defined inline with each activity. If step 2 fails, step 1's compensation runs automatically.

### 8.3 Workflow: `process-refund`

Triggered by: `POST /payments/{id}/refund`

```
Steps:
1. Activity: validate_refund_eligibility(order_id)
2. Activity: reverse_payment(payment_id)
3. Activity: release_inventory(order_id)
4. Activity: update_order_status(order_id, REFUNDED)
5. Activity: notify_customer(user_id, refund details)
```

### 8.4 Temporal Signal Example

When a payment gateway async webhook arrives, it sends a signal to the running workflow:

```
Signal: payment_result_received
Payload: { payment_id, status: "success" | "failed" }
```

The workflow is waiting on this signal (not polling). On receipt it proceeds to the next activity or runs compensation.

### 8.5 Temporal Setup

- Temporal server runs as a Docker container (uses `temporal_db` Postgres schema)
- One `workflow-service` Python worker that registers all workflows and activities
- Temporal Web UI available at `localhost:8088` for workflow inspection
- Python SDK: `temporalio`

---

## 9. Service Discovery — Consul

Every service registers itself with Consul on startup:

```
Service name:   order-service
Address:        order-service (Docker network hostname)
Port:           8000
Health check:   HTTP GET /health every 10s
Tags:           ["fastapi", "v1", "traefik.enable=true"]
```

Traefik watches Consul and automatically adds routes for any service tagged `traefik.enable=true`. No manual Traefik config per service.

Services can resolve other services by name via Consul DNS (`order-service.service.consul`) or Consul HTTP API. The `core-common` startup hook handles registration automatically — domain services do not write Consul code.

---

## 10. API Gateway — Traefik

- Single entry point for all clients
- Routes by path prefix: `/api/v1/users` → user-service, `/api/v1/orders` → order-service
- Handles TLS termination (in prod)
- JWT validation middleware (or delegates to each service's `AuthMiddleware`)
- Rate limiting per IP
- Dashboard at `localhost:8080` (dev)

---

## 11. Database Strategy

One logical database per service, all running on a single Postgres instance (resource-efficient for this hardware tier):

```
Postgres instance (port 5432)
  ├── users_db
  ├── products_db
  ├── orders_db
  ├── payments_db
  ├── notifications_db
  └── temporal_db        (Temporal's own schema)
```

Each service owns its schema entirely. Cross-service data needs go through APIs or events — never direct DB access across service boundaries.

Alembic migration base config lives in `core-common`. Each service's `env.py` extends it and only provides its own models.

Redis (single instance, port 6379):
- API response caching (product catalogue, user sessions)
- Rate limiter backing store for Traefik
- Celery broker (if background tasks are needed outside Temporal)

---

## 12. Authentication & Authorization Flow

```
1. Client → POST /api/v1/auth/login
2. API Gateway → routes to User Service
3. User Service validates credentials → issues JWT (access + refresh tokens)
4. Client stores JWT
5. Client → GET /api/v1/orders (with Authorization: Bearer <token>)
6. API Gateway validates JWT signature (shared secret / public key)
7. Request forwarded to Order Service with decoded user context header
8. Order Service AuthMiddleware (from core-common) reads user context
```

JWT payload:
```
sub         user_id (UUID)
email       user email
roles       list of roles (e.g. ["customer", "admin"])
exp         expiry timestamp
iat         issued at
jti         JWT ID (for revocation via Redis blacklist)
```

---

## 13. Event-Driven Flow Example — Place Order

```
Client
  └─ POST /api/v1/orders
       └─ API Gateway
            └─ Order Service
                 ├─ Creates Order record (status: PENDING)
                 ├─ Publishes order.created → RabbitMQ
                 └─ Starts Temporal workflow: place-order(order_id)

Temporal Workflow (place-order)
  ├─ Activity: reserve_inventory
  │     └─ HTTP call to Product Service internal API
  │     └─ Product Service updates inventory, publishes inventory.reserved
  │
  ├─ Activity: process_payment
  │     └─ HTTP call to Payment Service internal API
  │     └─ Payment Service calls mock gateway → async webhook signal back to Temporal
  │     └─ Temporal waits for signal (no polling)
  │     └─ On signal received (success): continue
  │     └─ On signal received (failed): compensate → release inventory → cancel order
  │
  ├─ Activity: confirm_order
  │     └─ HTTP call to Order Service → status: CONFIRMED
  │     └─ Publishes order.confirmed → RabbitMQ
  │
  └─ Activity: send_confirmation
        └─ Publishes notification.send → RabbitMQ
              └─ Notification Service consumes → sends email
```

---

## 14. Observability

### Logging
- `structlog` in JSON format on every service
- Correlation ID threaded through all log lines
- Log level configurable per environment via env var

### Metrics (optional, enable in dev/staging)
- Each FastAPI service exposes `GET /metrics` (Prometheus format)
- `prometheus-fastapi-instrumentator` auto-instruments all routes
- Grafana dashboard for latency, error rate, request rate per service

### Tracing (optional)
- `opentelemetry-sdk` + `opentelemetry-instrumentation-fastapi`
- Traces exported to Jaeger (`localhost:16686`)
- Correlation ID used as trace ID seed for cross-service linking

---

## 15. Docker Compose Layout

Two compose files to keep infra and services separated:

**`docker-compose.infra.yml`** — run once, rarely changes:
```
services:
  postgres
  redis
  rabbitmq         (management UI: localhost:15672)
  consul           (UI: localhost:8500)
  temporal         (UI: localhost:8088)
  traefik          (dashboard: localhost:8080)
```

**`docker-compose.yml`** — services, rebuilt on code changes:
```
services:
  user-service
  product-service
  order-service
  payment-service
  notification-service
  workflow-service
```

Each service image is built from a minimal Python 3.12 slim base. Services depend on infra being healthy (health-check depends_on).

---

## 16. Development Startup Order

```
1. docker compose -f docker-compose.infra.yml up -d
2. Wait for Postgres, Redis, RabbitMQ, Consul, Temporal to be healthy
3. Run Alembic migrations per service: alembic upgrade head
4. docker compose up -d
5. Traefik picks up services from Consul automatically
6. API available at http://localhost (port 80 via Traefik)
```

---

## 17. CI/CD — GitHub Actions Pipeline

```
Trigger: push to main or PR

Jobs:
  lint:       ruff + mypy on all packages
  test:       pytest per service (testcontainers for Postgres + RabbitMQ)
  build:      docker build per service
  push:       push to container registry (on main only)
  deploy:     docker compose pull + up on staging server (on main only)
```

---

## 18. Python Package Versions (pinned)

```
fastapi==0.115.x
uvicorn[standard]==0.30.x
pydantic==2.7.x
sqlalchemy==2.0.x
alembic==1.13.x
asyncpg==0.29.x           # async postgres driver
aio-pika==9.x             # async RabbitMQ (AMQP) client
temporalio==1.x           # Temporal Python SDK
redis[hiredis]==5.x
python-jose[cryptography]==3.x
structlog==24.x
httpx==0.27.x             # internal service-to-service calls
pytest==8.x
pytest-asyncio==0.23.x
testcontainers==4.x
ruff==0.4.x               # linter
mypy==1.10.x              # type checker
```

---

## 19. What Each Developer Needs to Know

When adding a new service:
1. Create the directory under `service folders/`
2. Install `core-common` and `msg-common` as local pip packages
3. Create domain model extending `BaseDomain`
4. Create schemas extending `BaseRequestSchema` / `BaseResponseSchema`
5. Create repository extending `BaseRepository` — add only custom queries
6. Create service extending `BaseService` — add only business logic, override hooks
7. Create controller extending `BaseController` — declare routes only
8. Declare message routes in `routes/message_routes.py` using `@router.consume`
9. Register with Consul in `main.py` (one function call from `core-common`)
10. Add Alembic migration

Grid, pagination, correlation ID, JWT auth, health checks, structured logging, RabbitMQ connection, DLQ handling — all inherited. Zero boilerplate.

---

## 20. Out of Scope (for this learning project)

- Frontend / admin UI
- CDN / file uploads (S3)
- Search service (Elasticsearch) — can be added later
- ML / recommendation engine
- Multi-region deployment
- mTLS between services (can add Consul Connect later)
