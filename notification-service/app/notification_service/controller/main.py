from __future__ import annotations
import dataclasses

import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from core_common.realtime import RealtimeHub
from notification_service.service import NotificationService
from msg_common.services.bus import EventBus

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    app = FastAPI(title="Notification Service")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    service = NotificationService()
    hub = RealtimeHub()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/notifications/{user_id}")
    async def list_notifications(user_id: str) -> list[dict]:
        return [dataclasses.asdict(item) for item in service.notifications if item.user_id == user_id]

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
