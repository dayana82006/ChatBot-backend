from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import logging
import asyncio
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
        logger.info("🟢 Admin WebSocket conectado")
        
        try:
            while True:
                # Mantener la conexión viva con ping/pong
                try:
                    # Esperar mensaje con timeout para enviar pings periódicos
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    logger.debug(f"Admin envió: {data}")
                    
                    # Aquí puedes procesar mensajes del admin si es necesario
                    # Por ejemplo, si el admin quiere responder a un usuario
                    
                except asyncio.TimeoutError:
                    # Enviar ping para mantener conexión viva
                    await websocket.send_json({"type": "ping"})
                    logger.debug("📡 Ping enviado a admin")
                    
        except WebSocketDisconnect:
            logger.info("🔴 Admin WebSocket desconectado")
            manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"❌ Error en WebSocket admin: {e}")
            manager.disconnect(websocket)
            
    elif user_id:
        await manager.connect(websocket, user_id)
        logger.info(f"🟢 Usuario WebSocket conectado: {user_id}")
        
        try:
            while True:
                try:
                    # Esperar mensaje con timeout
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    logger.debug(f"Usuario {user_id} envió: {data}")
                    
                    # Aquí puedes procesar mensajes del usuario si es necesario
                    
                except asyncio.TimeoutError:
                    # Enviar ping
                    await websocket.send_json({"type": "ping"})
                    logger.debug(f"📡 Ping enviado a usuario {user_id}")
                    
        except WebSocketDisconnect:
            logger.info(f"🔴 Usuario WebSocket desconectado: {user_id}")
            manager.disconnect(websocket, user_id)
        except Exception as e:
            logger.error(f"❌ Error en WebSocket usuario {user_id}: {e}")
            manager.disconnect(websocket, user_id)
            
    else:
        logger.warning("⚠️ Intento de conexión sin user_id ni is_admin")
        await websocket.close(code=1008, reason="user_id or is_admin required")