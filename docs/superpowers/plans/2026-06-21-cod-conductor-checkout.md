# COD Conductor Checkout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first real COD checkout slice with explicit payment selection, atomic inventory reservations, Conductor OSS orchestration boundaries, and async invoice/notification messaging.

**Architecture:** RabbitMQ carries `order.checkout.requested` into `workflow-service`, which starts a Conductor workflow. Conductor owns the critical saga task sequence: reserve inventory, authorize COD, confirm order, commit inventory, and compensation. RabbitMQ remains for post-confirmation fanout to invoice and notification consumers with retry/DLQ semantics.

**Tech Stack:** FastAPI, SQLAlchemy/Postgres, RabbitMQ event contracts, Conductor OSS HTTP API integration boundary, React/Vite, ReportLab for invoice PDFs.

---

### Task 1: Messaging Contracts

**Files:**
- Modify: `msg-common/app/msg_common/domain/envelope.py`
- Modify: `msg-common/app/msg_common/services/bus.py`
- Test: `msg-common/tests/test_event_bus.py`

- [ ] Add exchange/routing constants for `ecom.domain`, `order.checkout.requested`, `order.confirmed`, invoice, and notification routes.
- [ ] Add `idempotency_key` and `occurred_at` metadata to event envelopes while keeping existing tests compatible.
- [ ] Verify in-memory retry/DLQ behavior still works.

### Task 2: Product Reservations

**Files:**
- Modify: `product-service/app/product_service/domain/schemas.py`
- Modify: `product-service/app/product_service/services/service.py`
- Modify: `product-service/app/product_service/repo/repository.py`
- Modify: `product-service/app/product_service/controller/main.py`
- Test: `product-service/tests/test_product_catalog.py`

- [ ] Add reservation entities and service methods: `reserve_order`, `commit_reservation`, `release_reservation`.
- [ ] Ensure reservation is idempotent by `reservation_id`/`order_id`.
- [ ] Ensure reserving the last unit prevents another checkout from reserving it.
- [ ] Add HTTP endpoints that Conductor task workers can call.

### Task 3: Payment COD

**Files:**
- Modify: `payment-service/app/payment_service/domain/schemas.py`
- Modify: `payment-service/app/payment_service/services/service.py`
- Create: `payment-service/app/payment_service/repo/repository.py`
- Create: `payment-service/app/payment_service/controller/main.py`
- Create: `payment-service/tests/test_cod_payment.py`

- [ ] Add COD authorization model and idempotent authorization service.
- [ ] Add FastAPI endpoint for Conductor task workers.
- [ ] Persist payment status for owner dashboard/read models.

### Task 4: Order Workflow Boundary

**Files:**
- Modify: `order-service/app/order_service/domain/schemas.py`
- Modify: `order-service/app/order_service/services/service.py`
- Modify: `order-service/app/order_service/repo/repository.py`
- Modify: `order-service/app/order_service/controller/main.py`
- Test: `order-service/tests/test_order_checkout.py`

- [ ] Require `payment_method` and accept only `cod` for now.
- [ ] Publish `order.checkout.requested` with correlation and idempotency keys.
- [ ] Add confirm/fail endpoints for Conductor task workers.
- [ ] Keep order pending until workflow confirmation.

### Task 5: Conductor Workflow Service

**Files:**
- Modify: `workflow-service/app/workflow_service/services/service.py`
- Modify: `workflow-service/app/workflow_service/controller/main.py`
- Create: `workflow-service/app/workflow_service/services/conductor.py`
- Create: `workflow-service/app/workflow_service/workflows/order_checkout.json`
- Test: `workflow-service/tests/test_order_workflow.py`

- [ ] Define the checkout workflow JSON with critical tasks and compensation.
- [ ] Add an idempotent workflow starter for `order.checkout.requested`.
- [ ] Add task-handler functions that call product/payment/order services.
- [ ] Keep RabbitMQ out of internal critical task steps.

### Task 6: Invoice ReportLab

**Files:**
- Modify: `invoice-service/pyproject.toml`
- Modify: `invoice-service/app/invoice_service/services/service.py`
- Create: `invoice-service/app/invoice_service/controller/main.py`
- Create: `invoice-service/tests/test_invoice_pdf.py`

- [ ] Generate invoice PDFs using ReportLab.
- [ ] Persist invoice state and make generation idempotent by order ID.
- [ ] Prepare consumer-facing service API for async invoice generation.

### Task 7: Frontend Checkout And Owner Dashboard

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/lib/api/orders.ts`
- Modify: `frontend/src/App.test.tsx`
- Modify: `frontend/src/styles.css`

- [ ] Add payment method selector with COD enabled and other methods disabled.
- [ ] Submit checkout only when COD is selected.
- [ ] Show out-of-stock/backend errors without clearing the cart.
- [ ] Add owner/warehouse dashboard panels for order, inventory, invoice, and notification status.

### Task 8: Compose And Verification

**Files:**
- Modify: `docker-compose.infra.yml`
- Modify: `docker/service.Dockerfile`
- Modify: `docker/requirements-base.txt`

- [ ] Add Conductor OSS service and ports without conflicting with existing Traefik dashboard.
- [ ] Add ReportLab and service dependencies.
- [ ] Run focused Python and frontend tests.
- [ ] Run compose config validation.

