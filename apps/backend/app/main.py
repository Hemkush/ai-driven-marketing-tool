import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.core.logging_config import setup_logging
from app.api.routes import router
from app.api.mvp import router as mvp_router
from app.core.config import settings
from app.core.rate_limit import limiter

# Initialise structured JSON logging before anything else logs
setup_logging()

logger = logging.getLogger(__name__)

# Initialise Sentry (no-op if SENTRY_DSN is not set)
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            # Capture ERROR+ logs as Sentry breadcrumbs automatically
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
        # Capture 10% of transactions for performance monitoring (free tier safe)
        traces_sample_rate=0.1,
        # Never send raw prompt text or API keys to Sentry
        send_default_pii=False,
        environment=settings.sentry_environment,
    )
    logger.info("Sentry initialised", extra={"dsn_configured": True})

app = FastAPI(title="AI Marketing Tool API")

Instrumentator().instrument(app).expose(app, endpoint="/metrics")


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(mvp_router)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception",
        extra={"path": request.url.path, "method": request.method},
        exc_info=exc,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 2)
    level = logging.WARNING if response.status_code >= 500 else logging.INFO
    logger.log(
        level,
        f"{request.method} {request.url.path}",
        extra={
            "http_method": request.method,
            "http_path": request.url.path,
            "http_status": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response

@app.get("/health")
def health():
    return {"status": "ok"}
