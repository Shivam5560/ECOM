# M1 Shared Modules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the M1 shared packages, isolated auth service, user service, typed HTTP communication contracts, event contracts, and Docker Postgres infrastructure.

**Architecture:** The repo is a `uv` workspace with `app/` source roots and unique import packages. `core-common` owns HTTP contracts, auth validation contracts, response/error/pagination models, and typed service client infrastructure. `msg-common` owns event interfaces and in-memory event bus. `auth-service` owns OAuth/JWT/JWKS behavior and never calls `user-service`; `user-service` validates tokens through auth/JWKS abstractions.

**Tech Stack:** Python 3.12, uv workspace, FastAPI, Pydantic v2, SQLAlchemy async, Alembic, httpx, python-jose, passlib bcrypt, pytest, Docker Compose Postgres.

---

### Task 1: Workspace And Shared Contract Tests

**Files:**
- Create: `pyproject.toml`
- Create: `core-common/pyproject.toml`
- Create: `core-common/tests/test_models.py`
- Create: `msg-common/pyproject.toml`
- Create: `msg-common/tests/test_event_bus.py`

- [ ] **Step 1: Write failing shared-package tests**

Create tests that import `core_common` and `msg_common` before those packages exist.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest discover core-common/tests msg-common/tests -v`

Expected: import failures for `core_common` and `msg_common`.

- [ ] **Step 3: Add workspace and package metadata**

Create the root workspace and package `pyproject.toml` files using `uv_build`, `module-root = "app"`, and unique module names.

- [ ] **Step 4: Implement minimal shared package modules**

Implement response models, pagination, exceptions, auth context, service client contracts, event envelope, and in-memory event bus.

- [ ] **Step 5: Run shared-package tests**

Run: `PYTHONPATH=core-common/app:msg-common/app python3 -m unittest discover core-common/tests msg-common/tests -v`

Expected: all shared-package tests pass.

### Task 2: Core Common HTTP And Auth Contracts

**Files:**
- Create: `core-common/tests/test_service_client.py`
- Create: `core-common/app/http.py`
- Create: `core-common/app/auth.py`
- Create: `core-common/app/middleware.py`

- [ ] **Step 1: Write failing tests for service resolution and HTTP error mapping**

Tests cover static service resolution, typed response parsing, correlation propagation, and service call failures.

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=core-common/app python3 -m unittest core-common/tests/test_service_client.py -v`

Expected: missing `core_common.http` functionality.

- [ ] **Step 3: Implement the minimal HTTP contracts and client**

Implement protocols, resolver, request context, and `HttpServiceClient`.

- [ ] **Step 4: Run core-common tests**

Run: `PYTHONPATH=core-common/app python3 -m unittest discover core-common/tests -v`

Expected: all `core-common` tests pass where external dependencies are not required.

### Task 3: Auth Service Scaffold

**Files:**
- Create: `auth-service/pyproject.toml`
- Create: `auth-service/app/main.py`
- Create: `auth-service/app/config.py`
- Create: `auth-service/app/security.py`
- Create: `auth-service/app/schemas.py`
- Create: `auth-service/tests/test_security.py`

- [ ] **Step 1: Write failing tests for password hashing, JWT claims, and JWKS shape**

Tests cover the service-owned security API without requiring the FastAPI server to run.

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=core-common/app:auth-service/app python3 -m unittest discover auth-service/tests -v`

Expected: missing `auth_service` modules.

- [ ] **Step 3: Implement auth security and FastAPI app scaffold**

Implement isolated token/JWKS behavior and endpoint skeletons. Keep `auth-service` free of `user-service` imports or clients.

- [ ] **Step 4: Run auth service tests**

Run: `PYTHONPATH=core-common/app:auth-service/app python3 -m unittest discover auth-service/tests -v`

Expected: auth security tests pass when dependencies are available.

### Task 4: User Service Scaffold

**Files:**
- Create: `user-service/pyproject.toml`
- Create: `user-service/app/main.py`
- Create: `user-service/app/schemas.py`
- Create: `user-service/app/auth_client.py`
- Create: `user-service/app/service.py`
- Create: `user-service/tests/test_user_service.py`

- [ ] **Step 1: Write failing tests for profile ownership and event publishing**

Tests cover creating a user profile from token subject and publishing `user.registered`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=core-common/app:msg-common/app:user-service/app python3 -m unittest discover user-service/tests -v`

Expected: missing `user_service` modules.

- [ ] **Step 3: Implement user service logic and FastAPI app scaffold**

Implement service-level profile creation and endpoint skeletons. User service may depend on auth validation contracts but auth service must not depend on user service.

- [ ] **Step 4: Run user service tests**

Run: `PYTHONPATH=core-common/app:msg-common/app:user-service/app python3 -m unittest discover user-service/tests -v`

Expected: user service tests pass.

### Task 5: Docker Postgres Infrastructure

**Files:**
- Create: `docker-compose.infra.yml`
- Create: `infra/postgres/init/001-create-databases.sql`

- [ ] **Step 1: Add Docker Compose and init SQL**

Define one Postgres container and create `auth_db`, `users_db`, `auth_test_db`, and `users_test_db`.

- [ ] **Step 2: Validate compose syntax**

Run: `docker compose -f docker-compose.infra.yml config`

Expected: compose renders successfully when Docker is available.

### Task 6: Final Verification

**Files:**
- Verify all created files.

- [ ] **Step 1: Run all stdlib-compatible tests**

Run: `PYTHONPATH=core-common/app:msg-common/app:auth-service/app:user-service/app python3 -m unittest discover -v`

Expected: all tests that do not require missing third-party dependencies pass.

- [ ] **Step 2: Report dependency-limited checks**

Document any checks blocked by missing `uv`, Python 3.12, or third-party dependencies on the host.
