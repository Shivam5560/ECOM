#!/bin/bash

# Sync workspace dependencies ONCE
echo "Syncing workspace dependencies..."
uv sync --python 3.12 --all-packages

# Start services
echo "Starting backend microservices..."

echo "Starting auth-service on 8001..."
cd auth-service && uv run --python 3.12 uvicorn auth_service.controller.main:create_app --factory --host 0.0.0.0 --port 8001 &
AUTH_PID=$!
cd /home/gopal/Desktop/ECOM

echo "Starting user-service on 8002..."
cd user-service && uv run --python 3.12 uvicorn user_service.controller.main:create_app --factory --host 0.0.0.0 --port 8002 &
USER_PID=$!
cd /home/gopal/Desktop/ECOM

echo "Starting product-service on 8003..."
cd product-service && uv run --python 3.12 uvicorn product_service.controller.main:create_app --factory --host 0.0.0.0 --port 8003 &
PRODUCT_PID=$!
cd /home/gopal/Desktop/ECOM

echo "Starting order-service on 8004..."
cd order-service && uv run --python 3.12 uvicorn order_service.controller.main:create_app --factory --host 0.0.0.0 --port 8004 &
ORDER_PID=$!
cd /home/gopal/Desktop/ECOM

echo "Starting notification-service on 8005..."
cd notification-service && uv run --python 3.12 uvicorn notification_service.controller.main:create_app --factory --host 0.0.0.0 --port 8005 &
NOTIF_PID=$!
cd /home/gopal/Desktop/ECOM

echo "Starting workflow-service on 8006..."
cd workflow-service && uv run --python 3.12 uvicorn workflow_service.controller.main:create_app --factory --host 0.0.0.0 --port 8006 &
WORKFLOW_PID=$!
cd /home/gopal/Desktop/ECOM

echo "Services started."
echo "Auth: $AUTH_PID, User: $USER_PID, Product: $PRODUCT_PID, Order: $ORDER_PID, Notif: $NOTIF_PID, Workflow: $WORKFLOW_PID"

wait
