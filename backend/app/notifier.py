"""Firebase Cloud Messaging push notifications."""

import logging
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, messaging

from .database import get_db

logger = logging.getLogger(__name__)

SERVICE_ACCOUNT_PATH = Path("/app/certs/firebase-service-account.json")

_initialized = False


def _init_firebase():
    global _initialized
    if _initialized:
        return
    cred = credentials.Certificate(str(SERVICE_ACCOUNT_PATH))
    firebase_admin.initialize_app(cred)
    _initialized = True


async def register_token(token: str):
    """Store a device token for push notifications."""
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR IGNORE INTO device_tokens (token) VALUES (?)", (token,)
        )
        await db.commit()
    finally:
        await db.close()


async def send_push(title: str, body: str):
    """Send a push notification to all registered devices."""
    _init_firebase()

    db = await get_db()
    try:
        cursor = await db.execute("SELECT token FROM device_tokens")
        rows = await cursor.fetchall()
    finally:
        await db.close()

    tokens = [r["token"] for r in rows]
    if not tokens:
        logger.info("No device tokens registered, skipping push")
        return

    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        tokens=tokens,
        android=messaging.AndroidConfig(priority="high"),
        apns=messaging.APNSConfig(
            headers={
                "apns-priority": "10",
                "apns-push-type": "alert",
            },
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    alert=messaging.ApsAlert(title=title, body=body),
                    sound="default",
                    custom_data={"interruption-level": "time-sensitive"},
                ),
            ),
        ),
    )

    try:
        response = messaging.send_each_for_multicast(message)
        logger.info(f"Push sent: {response.success_count} success, {response.failure_count} failure")

        # Clean up invalid tokens
        if response.failure_count > 0:
            db = await get_db()
            try:
                for i, send_response in enumerate(response.responses):
                    if not send_response.success:
                        err = send_response.exception
                        if err and (
                            "UNREGISTERED" in str(err)
                            or "INVALID_ARGUMENT" in str(err)
                        ):
                            await db.execute(
                                "DELETE FROM device_tokens WHERE token = ?",
                                (tokens[i],),
                            )
                await db.commit()
            finally:
                await db.close()

    except Exception as e:
        logger.error(f"Push notification failed: {e}")
