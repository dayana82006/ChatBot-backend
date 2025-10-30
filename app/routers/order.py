from fastapi import APIRouter, HTTPException
from app.queries.orderService import get_order_summary, update_order_status

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.get("/{pedido_id}")
def obtener_pedido(pedido_id: int):
    detalles = get_order_summary(pedido_id)
    if not detalles:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return {"pedido_id": pedido_id, "detalles": detalles}

@router.put("/{pedido_id}/estado")
def cambiar_estado(pedido_id: int, nuevo_estado: str):
    update_order_status(pedido_id, nuevo_estado)
    return {"message": f"Estado del pedido {pedido_id} actualizado a '{nuevo_estado}'"}