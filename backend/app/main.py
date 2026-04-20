"""
main.py — FastAPI application entry point.
Registers all routers. Configures rate limiting. Sets up lifespan hooks.

Windows dev note: psycopg3 (AsyncPostgresSaver) requires SelectorEventLoop.
Run uvicorn with --loop asyncio on Windows:
  uvicorn app.main:app --reload --loop asyncio
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter
from app.core.config import settings
from app.api.v1.endpoints import auth, chat, profile
import app.models  # noqa: F401 — registers all 6 SQLAlchemy mappers at startup


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialise AsyncPostgresSaver checkpointer and compile LangGraph."""
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from app.agents.core_graph import build_graph

    async with AsyncPostgresSaver.from_conn_string(
        settings.checkpoint_db_url
    ) as checkpointer:
        await checkpointer.setup()
        app.state.graph = build_graph(checkpointer)
        yield


app = FastAPI(
    title="FYP Career Guidance API",
    description="AI-Assisted Academic Career Guidance System for Karachi students.",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — explicit origins required when allow_credentials=True
# Add your deployed frontend URL here before production release
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8081",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Standard error response format ────────────────────────────────────────
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error_code": "INTERNAL_ERROR",
                 "message": "An unexpected error occurred.",
                 "details": []},
    )


# ── Register routers ───────────────────────────────────────────────────────
app.include_router(auth.router,    prefix="/api/v1")
app.include_router(profile.router, prefix="/api/v1")
app.include_router(chat.router,    prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "fyp-career-guidance-api"}
