from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..database import get_db
from ..models import NotificationResponse, PriceHistoryPoint
from ..notifier import register_token

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/flights/{flight_id}/history", response_model=list[PriceHistoryPoint])
async def get_history(flight_id: int, limit: int = Query(500)):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT price, checked_at FROM price_history "
            "WHERE tracked_flight_id = ? ORDER BY checked_at ASC LIMIT ?",
            (flight_id, limit),
        )
        rows = await cursor.fetchall()
    finally:
        await db.close()
    return [PriceHistoryPoint(price=r["price"], checked_at=r["checked_at"]) for r in rows]


@router.get("/notifications", response_model=list[NotificationResponse])
async def get_notifications():
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM notifications WHERE is_read = 0 ORDER BY created_at DESC LIMIT 50"
        )
        rows = await cursor.fetchall()
    finally:
        await db.close()
    return [
        NotificationResponse(
            id=r["id"],
            tracked_flight_id=r["tracked_flight_id"],
            message=r["message"],
            old_price=r["old_price"],
            new_price=r["new_price"],
            created_at=r["created_at"],
            is_read=bool(r["is_read"]),
        )
        for r in rows
    ]


@router.patch("/notifications/{notification_id}/read", status_code=204)
async def mark_read(notification_id: int):
    db = await get_db()
    try:
        await db.execute(
            "UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,)
        )
        await db.commit()
    finally:
        await db.close()


class TokenRequest(BaseModel):
    token: str


@router.post("/device-tokens", status_code=201)
async def register_device_token(req: TokenRequest):
    await register_token(req.token)
    return {"status": "registered"}
