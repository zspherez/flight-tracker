"""Shared slowapi limiter.

Per-IP cap of 3 req/sec on fli-bound endpoints — one-third of fli's global
10 req/sec budget, so a single client can't starve the upstream.

Real client IP comes from X-Forwarded-For; uvicorn must run with
--proxy-headers --forwarded-allow-ips=127.0.0.1 since Caddy fronts on loopback.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=[])

FLI_BOUND = "3/second"
