"""
limiter.py — Shared slowapi Limiter instance.
Both main.py (app.state.limiter) and chat.py (@limiter.limit) must use
the SAME instance for rate limiting to work correctly.
Never create a second Limiter() anywhere.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
