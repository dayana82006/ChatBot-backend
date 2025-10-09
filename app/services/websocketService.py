import logging
from typing import Dict, Set
from fastapi import WebSocket
import json

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.admin_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, user_id: str = None):
        await websocket.accept()

        if user_id:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
            logger.info(f"WebSocket conectado para user_id: {user_id}")
        else:
            self.admin_connections.add(websocket)
            logger.info("WebSocket admin conectado")

    def disconnect(self, websocket: WebSocket, user_id: str = None):
        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            logger.info(f"WebSocket desconectado para user_id: {user_id}")
        else:
            self.admin_connections.discard(websocket)
            logger.info("WebSocket admin desconectado")

    async def send_message_to_user(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                    logger.debug(f"Mensaje enviado a {user_id}: {message}")
                except Exception as e:
                    logger.error(f"Error enviando mensaje a {user_id}: {e}")
                    disconnected.add(connection)

            for conn in disconnected:
                self.active_connections[user_id].discard(conn)

    async def broadcast_to_admins(self, message: dict):
        disconnected = set()
        for connection in self.admin_connections:
            try:
                await connection.send_json(message)
                logger.debug(f"Mensaje broadcast a admin: {message}")
            except Exception as e:
                logger.error(f"Error enviando mensaje a admin: {e}")
                disconnected.add(connection)

        for conn in disconnected:
            self.admin_connections.discard(conn)

    async def notify_new_message(self, user_id: str, chat_id: int, role: str, text: str, channel: str = "web"):
        message = {
            "type": "new_message",
            "data": {
                "user_id": user_id,
                "chat_id": chat_id,
                "role": role,
                "text": text,
                "channel": channel
            }
        }

        await self.send_message_to_user(user_id, message)
        await self.broadcast_to_admins(message)

manager = ConnectionManager()
