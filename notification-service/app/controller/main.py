from __future__ import annotations

from core_common.realtime import RealtimeHub
from notification_service.service import NotificationService


def create_app():
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect

    app = FastAPI(title="notification-service")
    service = NotificationService()
    hub = RealtimeHub()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/notifications/{user_id}")
    async def list_notifications(user_id: str) -> list[dict]:
        return [item.__dict__ for item in service.notifications if item.user_id == user_id]

    @app.websocket("/ws/notifications/{user_id}")
    async def notification_socket(websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        hub.connect(user_id, websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            hub.disconnect(user_id, websocket)

    return app
