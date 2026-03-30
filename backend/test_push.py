#!/usr/bin/env python3
import asyncio
from app.notifier import send_push

asyncio.run(send_push("Test Alert", "CHS→EWR UA674 dropped to $450 (was $478)"))
