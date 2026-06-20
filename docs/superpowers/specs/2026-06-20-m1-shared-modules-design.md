# M1 Shared Modules Design

Date: 2026-06-20

## Goal

Milestone 1 builds the reusable foundation for the e-commerce microservice platform before the rest of the domain services are implemented in parallel.

The milestone creates installable shared Python packages, one OAuth-focused auth service, one user service that proves the framework pattern, and Docker-backed Postgres test databases that mirror the intended service isolation model.

## Scope

M1 includes:

- `core-common` as an installable `pyproject.toml` package.
- `msg-common` as an installable `pyproject.toml` package.
- `auth-service` for OAuth/JWT ownership.
- `user-service` as the first domain service using the shared framework contracts.
- REST/HTTP inter-service communication using typed Python clients over `httpx`.
- Postgres via Docker with separate runtime and test databases per service.
- Unit and service tests for shared contracts, auth behavior, user behavior, and communication seams.

M1 excludes:

- RabbitMQ concrete implementation.
- Temporal workflows.
- Consul registration and discovery.
- Traefik gateway.
- Product, order, payment, notification, and workflow services.
- gRPC implementation.

## Repository Shape

```text
ecommerce-platform/
├── pyproject.toml
├── core-common/
│   ├── app/
│   │   └── core_common/
│   ├── tests/
│   └── pyproject.toml
├── msg-common/
│   ├── app/
│   │   └── msg_common/
│   ├── tests/
│   └── pyproject.toml
├── service folders/
│   ├── auth-service/
│   │   ├── app/
│   │   │   └── auth_service/
│   │   ├── migrations/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   └── user-service/
│       ├── app/
│       │   └── user_service/
│       ├── migrations/
│       ├── tests/
│       ├── Dockerfile
│       └── pyproject.toml
├── docker-compose.infra.yml
└── ecommerce-microservice-spec.md
```

## Shared Package Strategy

Both shared modules are real Python packages from the start. Services consume them as workspace dependencies during development.

Root workspace shape:

```toml
[project]
name = "ecommerce-platform"
version = "0.1.0"
requires-python = ">=3.12"

[tool.uv]
package = false

[tool.uv.workspace]
members = [
  "core-common",
  "msg-common",
  "auth-service",
  "user-service"
]
```

Example service dependency shape:

```toml
[project]
dependencies = [
  "core-common",
  "msg-common"
]

[tool.uv.sources]
core-common = { workspace = true }
msg-common = { workspace = true }
```

This keeps each service independently testable while allowing the shared contracts to evolve in one monorepo.

### `uv` Layout Compatibility

The repo uses `app/` as the source root inside each package, but the import packages must remain unique:

- `core-common/app`
- `msg-common/app`
- `auth-service/app`
- `user-service/app`

Do not make every package importable as top-level `app`; editable installs and workspace commands would collide.

Each package configures the `uv_build` backend with its `app/` module root:

```toml
[build-system]
requires = ["uv_build>=0.11.23,<0.12"]
build-backend = "uv_build"

[tool.uv.build-backend]
module-root = "app"
module-name = "core_common"
```

The `module-name` changes per package. For example, `msg-common` uses `msg_common`, `auth-service` uses `auth_service`, and `user-service` uses `user_service`.

## `core-common`

`core-common` is hybrid and interface-first. It provides strict contracts for common service structure, but it does not own service-specific database schemas, SQLAlchemy models, migrations, or business logic.

It includes:

- Response envelope models.
- Error envelope models.
- Shared exception hierarchy.
- Pagination and grid request models.
- Paged response models.
- Base service/controller protocols.
- Auth context models.
- Token verification protocols.
- Correlation ID helpers and middleware.
- Inter-service communication contracts and HTTP implementation.

### Domain Model Boundary

The original architecture spec described `BaseDomain` as a Pydantic model for ORM-mapped entities. M1 corrects this design.

Service entities are SQLAlchemy 2.0 declarative models owned by each service. Pydantic v2 is used for request and response DTOs.

`core-common` may provide simple mixins or protocols later, but M1 does not force a shared concrete ORM base.

### Persistence Boundary

Persistence is interface-first in M1.

`core-common` defines repository and service contracts, but each service owns:

- SQLAlchemy models.
- Database URL.
- Async session setup.
- Alembic migrations.
- Concrete repositories.
- Test database fixtures.

This supports the platform rule that each service owns its schema and database boundary.

## Inter-Service Communication

M1 uses REST/HTTP with typed Python clients over `httpx`. This is the Python equivalent of a Feign-style client.

Business logic must not call raw URLs directly. Service-to-service calls go through typed clients backed by shared `core-common` communication primitives.

`core-common` includes:

- `ServiceResolver` protocol.
- `StaticServiceResolver` implementation for local development and tests.
- `ServiceClient` protocol.
- `HttpServiceClient` implementation using `httpx.AsyncClient`.
- Request timeout handling.
- Correlation ID propagation.
- Authorization header propagation.
- Pydantic response parsing.
- Shared service-call exceptions.

Example domain-specific client shape:

```python
class AuthClientProtocol(Protocol):
    async def introspect_token(self, token: str) -> TokenIntrospection: ...


class HttpAuthClient:
    def __init__(self, service_client: ServiceClient) -> None:
        self.service_client = service_client

    async def introspect_token(self, token: str) -> TokenIntrospection:
        return await self.service_client.post(
            "auth-service",
            "/internal/auth/introspect",
            json={"token": token},
            response_model=TokenIntrospection,
        )
```

### Future Adapters

Consul can later replace `StaticServiceResolver`.

gRPC can later be added as another adapter if strict IDL contracts or performance requirements justify it. M1 keeps the interface generic enough to avoid rewriting service business logic.

## `msg-common`

`msg-common` is interface-only for external messaging in M1.

It includes:

- `EventEnvelope`.
- `EventPublisher` protocol.
- `EventConsumer` protocol.
- `EventBus` protocol.
- Route metadata and decorator shape.
- `InMemoryEventBus` for tests and local development.

It does not include RabbitMQ, `aio-pika`, retry queues, or DLQ wiring in M1.

RabbitMQ will be a later adapter that implements the same interfaces.

## `auth-service`

`auth-service` owns OAuth/JWT behavior.

M1 responsibilities:

- Register and store credentials needed for authentication.
- Hash and verify passwords.
- Issue JWT access tokens.
- Provide JWKS and optional token introspection endpoints for internal service validation.
- Expose OAuth/login endpoints.
- Own `auth_db` and `auth_test_db`.

Initial endpoints:

- `POST /auth/register`
- `POST /auth/login`
- `POST /oauth/token`
- `GET /.well-known/jwks.json`
- `POST /internal/auth/introspect`
- `GET /health`
- `GET /ready`

Both `/auth/login` and `/oauth/token` exist in M1. `/auth/login` supports simple JSON clients. `/oauth/token` supports OAuth2 password-form style clients. Both use the same token issuing service internally.

JWT signing uses an asymmetric key pair in M1 so services can validate tokens through a JWKS endpoint without sharing the signing secret.

Registration flow:

1. Client calls `POST /auth/register`.
2. `auth-service` validates and stores credentials in `auth_db`.
3. `auth-service` returns an auth identity subject and an access token.

`auth-service` does not call `user-service`. It remains isolated and owns only credentials, OAuth/JWT token issuance, JWKS exposure, and token introspection.

## `user-service`

`user-service` is the first domain service implementation using `core-common`.

M1 responsibilities:

- Create and manage user profile records.
- Demonstrate controller, service, repository, pagination, response envelope, and error handling patterns.
- Validate access tokens using `auth-service` JWKS or introspection through typed auth clients.
- Publish `user.registered` through the `msg-common` `EventBus` interface.
- Own `users_db` and `users_test_db`.

Initial endpoints:

- `POST /users`
- `GET /users`
- `GET /users/{user_id}`
- `PATCH /users/{user_id}`
- `DELETE /users/{user_id}`
- `GET /health`
- `GET /ready`

Deletes are soft deletes in M1. User records get a nullable `deleted_at` timestamp, and list/detail endpoints exclude deleted records by default.

Profile creation is separate from auth registration in M1. A client first obtains an auth identity from `auth-service`, then calls `user-service` with the access token to create or update the user profile. `user-service` validates the token and uses the token subject as the profile owner.

## Database Design

M1 uses one Dockerized Postgres instance with separate logical databases.

Runtime databases:

- `auth_db`
- `users_db`

Test databases:

- `auth_test_db`
- `users_test_db`

Each service runs its own migrations against its own runtime and test database.

Tests should run against Postgres, not SQLite, so behavior matches the intended deployment model. Test setup runs migrations once per test session and truncates service-owned tables between tests.

## Docker Compose

`docker-compose.infra.yml` starts the infrastructure needed for M1:

- Postgres.

Redis, RabbitMQ, Consul, Temporal, Traefik, Prometheus, and Grafana remain out of scope until the milestone that needs them.

The Postgres container initialization must create:

- `auth_db`
- `users_db`
- `auth_test_db`
- `users_test_db`

## Testing Strategy

Shared packages:

- Validate response envelope behavior.
- Validate pagination/grid models.
- Validate exception mapping.
- Validate correlation ID propagation helpers.
- Validate `HttpServiceClient` behavior using mocked `httpx` transport.
- Validate `InMemoryEventBus`.

`auth-service`:

- Login/token success.
- Invalid credential handling.
- Token introspection success.
- JWKS endpoint exposes public signing keys.
- Expired/invalid token behavior.
- Database-backed credential persistence.

`user-service`:

- Create user.
- List users with pagination.
- Retrieve user by ID.
- Patch user.
- Soft delete user.
- Publish `user.registered` through injected `EventBus`.
- Validate token context through fake JWKS/introspection clients in tests.

Integration-style tests:

- Run service tests against Docker Postgres test databases.
- Use static service resolver and mocked HTTP transports for inter-service tests unless both services are explicitly started in a later milestone.

## Error Handling

All HTTP services return a consistent error shape from `core-common`.

Service-call errors are normalized into shared exceptions:

- `ServiceCallError`
- `ServiceUnavailableError`
- `UnauthorizedError`
- `ForbiddenError`
- `ValidationError`
- `NotFoundError`

The internal HTTP client maps transport errors, non-2xx responses, malformed responses, and timeout errors into these exceptions.

## Observability Basics

M1 includes lightweight observability primitives only:

- Correlation ID generation and propagation.
- JSON-friendly log context helpers.
- Health and readiness endpoint helpers.

Full structured logging, OpenTelemetry, Prometheus, and dashboarding are deferred.

## Implementation Order

1. Create `core-common` package and tests.
2. Create `msg-common` package and tests.
3. Add Docker Postgres infrastructure and database initialization.
4. Create `auth-service` package, migrations, endpoints, and tests.
5. Create `user-service` package, migrations, endpoints, and tests.
6. Add cross-service typed client examples/tests.
7. Run package and service test suites.

## Implementation Planning Decisions

The following details are left to the implementation plan because they affect task ordering, not architecture:

- Exact package manager command workflow.
- Exact Alembic command wrappers.
- Whether service containers are added in M1 or only local Python test commands plus Postgres compose are used.
