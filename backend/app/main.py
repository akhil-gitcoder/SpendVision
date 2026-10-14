"""FastAPI application entrypoint."""
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.utils.seed import run_seed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="AI Personal Finance Dashboard API",
    description="Backend for a medium-scale AI-powered personal finance dashboard.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.middleware("http")
async def protect_browser_requests(
    request: Request,
    call_next,
):
    # Browser actions must come from a trusted frontend origin.
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = request.headers.get("origin")

        if origin not in settings.cors_origin_list:
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "Untrusted request origin."
                },
            )

    response = await call_next(request)

    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"

    return response


@app.on_event("startup")
def on_startup() -> None:
    # create_all is sufficient for this MVP (no migration history needed yet).
    # For a production app, this would be replaced by Alembic migrations.
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        run_seed(db)
    finally:
        db.close()
    if not settings.is_ai_configured:
        logger.warning(
            "AI_PROVIDER/AI_API_KEY not configured - AI features will use "
            "deterministic fallback behavior instead of calling an LLM."
        )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Never leak stack traces, DB connection strings, or API keys to the client.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred."})


app.include_router(api_router)


@app.get("/")
def root():
    return {"name": "AI Personal Finance Dashboard API", "docs": "/docs"}
