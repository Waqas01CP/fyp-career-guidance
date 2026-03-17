"""
auth_service.py — Higher-level auth helpers used by endpoints.
JWT generation and validation live in core/security.py.
This service wraps them if business logic grows.
"""
# Currently thin — endpoints call core/security.py directly.
# Add token refresh, session invalidation, etc. here when needed.
