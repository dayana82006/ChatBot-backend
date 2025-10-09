from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import logging
from app.services.websocketService import manager

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Query(None),
    is_admin: bool = Query(False)
):
    if is_admin:
        await manager.connect(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket)
    elif user_id:
        await manager.connect(websocket, user_id)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id)
    else:
        await websocket.close(code=1008, reason="user_id or is_admin required")
