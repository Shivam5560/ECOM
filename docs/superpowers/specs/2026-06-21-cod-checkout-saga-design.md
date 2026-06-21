# COD Checkout Saga Design

## Goal

Build the first production-shaped checkout slice: a user explicitly selects Cash on Delivery, the system reserves inventory atomically, confirms the order through a Conductor OSS saga, and emits reliable post-confirmation events for invoice and notification processing.

## Scope

This design covers:

- Frontend checkout UI for payment method selection.
- COD as the only enabled payment option, with other methods visible but disabled.
- Real backend APIs only; seeded data may exist only through migration/seed scripts.
- Atomic inventory reservation during checkout.
- Conductor OSS orchestration for the critical order flow.
- Durable RabbitMQ messaging for long-running side effects.
- Idempotent invoice and notification consumers with retry and DLQ support.

This design does not cover:

- Real card/UPI/net-banking gateway integrations.
- Support UI for replaying DLQ messages.
- Manual production support tooling beyond queue/DLQ topology and message idempotency.

## User Experience

The cart does not reserve stock. Users may add available products to the cart, but stock is reserved only when checkout starts.

At checkout, the user sees payment methods:

- Cash on Delivery: enabled and selectable.
- Other payment methods: visible but disabled.

COD is not selected automatically. The user must choose it before submitting checkout.

If stock is no longer available during checkout, the checkout fails with an out-of-stock message. The cart should refresh product stock where possible and keep the user on the cart/checkout surface.

After successful confirmation, the UI shows the confirmed order state, listens for realtime notifications, and exposes invoice download once invoice generation succeeds. Invoice generation is asynchronous, so the UI may show a pending invoice state first.

## Critical Saga

The critical transaction path is:

1. User selects COD and submits checkout.
2. `order-service` creates a pending order with an idempotency key/correlation ID.
3. `order-service` publishes `order.checkout.requested`.
4. `workflow-service` consumes `order.checkout.requested` and starts a Conductor OSS checkout workflow.
5. `product-service` atomically reserves inventory.
6. `payment-service` authorizes the selected payment method as COD.
7. `order-service` confirms the order.
8. `product-service` commits the inventory reservation as sold.
9. System publishes `order.confirmed`.

Inventory reservation must be atomic. If only one item remains and User A checks out first, User B must either see out of stock after refresh or receive an out-of-stock error at checkout.

## Compensation

If a critical step fails before order confirmation:

- Release any inventory reservation.
- Mark payment authorization failed/cancelled if applicable.
- Mark order failed/cancelled.
- Publish a checkout failure event for observability and user notification.

Notification failure must not cancel the order.

Invoice generation failure must not cancel the order.

## Async Side Effects

After `order.confirmed`, invoice and notification run in parallel:

- `invoice-service` consumes invoice generation messages, persists invoice metadata, generates PDF, and publishes success/failure.
- `notification-service` consumes notification messages, persists notification records, and pushes realtime WebSocket events to connected users.

Both services must use durable queues, retries, DLQs, and idempotent consumers. A production support person can later inspect/replay DLQ messages outside the app UI.

## Messaging Reliability

RabbitMQ topology should use durable exchanges and queues. Messages should include:

- `event_id`
- `event_type`
- `correlation_id`
- `idempotency_key`
- `source_service`
- `occurred_at`
- Payload version

Consumers must record processed message IDs or business idempotency keys before acknowledging messages. Duplicate delivery should be harmless.

For zero-message-loss behavior around database writes and publishing, services that update their own database and publish events should use an outbox pattern or an equivalent transactional persistence boundary.

## Service Responsibilities

### Frontend

- Fix currently non-working buttons where they are part of checkout/admin/order flow.
- Use real API calls through the gateway.
- Show payment method selector with COD enabled and other methods disabled.
- Submit checkout only after COD is selected.
- Display stock and checkout errors from backend responses.
- Listen for realtime notifications from `notification-service`.
- Show invoice pending/available states.
- Provide an owner/warehouse dashboard that visualizes new orders, pending confirmations, confirmed orders, inventory/reservation state, invoice status, notification status, and operational failures that need attention.

### Order Service

- Persist pending, confirmed, failed, and cancelled orders.
- Validate authenticated user.
- Reprice lines from product catalog.
- Start checkout workflow or publish checkout requested event.
- Expose order status and invoice link/status fields.
- Support idempotent checkout by correlation/idempotency key.

### Product Service

- Own stock and reservation state.
- Provide atomic reservation API/activity.
- Reject checkout when stock cannot be reserved.
- Commit reservation after order confirmation.
- Release reservation on compensation.

### Payment Service

- Expose COD authorization.
- Persist payment records with method, status, order ID, user ID, amount, and idempotency key.
- Treat COD authorization as a real payment state, not a mock.
- Leave room for future payment methods without changing order workflow contracts.

### Workflow Service

- Own Conductor OSS checkout workflow definition.
- Consume durable `order.checkout.requested` events and start Conductor workflows idempotently.
- Execute critical saga steps and compensations.
- Publish confirmed/failure events after terminal workflow state.
- Keep invoice and notification outside the critical transaction.

The critical saga uses Conductor task workers for inventory reservation, COD authorization, order confirmation, inventory commit, and compensation. RabbitMQ is not used between those internal critical steps.

### Invoice Service

- Consume `order.confirmed` or `invoice.generate.requested`.
- Generate PDF asynchronously with ReportLab.
- Persist invoice status and document location.
- Retry transient failures and route repeated failures to DLQ.
- Be idempotent for the same order/invoice key.

### Owner/Warehouse Dashboard

- Show order queue grouped by status: pending, reserving inventory, payment authorized, confirmed, failed, cancelled, ready to pack, and completed.
- Show stock and reservation pressure so the owner can see low stock, reserved stock, committed stock, and failed reservations.
- Show invoice status per order: pending, generated, failed/retry, or DLQ.
- Show notification status per order: pending, sent, failed/retry, or DLQ.
- Keep developer/support controls such as DLQ replay outside this UI unless a later admin-ops screen is explicitly designed.
- Use service APIs and read models; do not rely on frontend-seeded dashboard data.

### Notification Service

- Consume order/payment/invoice notification events.
- Persist notifications.
- Push realtime notifications over WebSocket.
- Retry transient failures and route repeated failures to DLQ.
- Be idempotent for duplicate messages.

## Data And Seed Policy

Runtime UI and service behavior must use real APIs and persisted service data.

Seeded data is allowed only in migration or seed SQL scripts. Frontend fallback demo data should not hide backend failures for production-shaped workflows.

## Acceptance Criteria

- User must explicitly select COD before checkout.
- Other payment methods are visible but disabled.
- Checkout reserves inventory atomically.
- Concurrent checkout cannot oversell the last stock unit.
- Failed critical checkout releases reservation and marks order failed/cancelled.
- Successful checkout confirms order and commits inventory.
- Invoice and notification failures do not cancel confirmed orders.
- Invoice and notification consumers are idempotent and use retry/DLQ behavior.
- UI reflects checkout success/failure, realtime notifications, and invoice pending/available states using real APIs.
- Owner/warehouse dashboard shows real order, inventory, invoice, and notification operational state.

## Open Implementation Decisions

- Exact RabbitMQ exchange naming and routing key convention.
- Whether outbox dispatch starts as a poller inside each service or a shared worker pattern.
