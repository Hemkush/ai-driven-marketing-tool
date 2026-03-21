from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.api.mvp_routes import router as mvp_router
from app.core.config import settings
from fastapi.responses import JSONResponse
from fastapi import Request
import time
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator
from app.core.rate_limit import limiter

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
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

@app.middleware("http")
async def log_requests(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 2)
    print(f"{request.method} {request.url.path} -> {response.status_code} [{duration_ms}ms]")
    return response

@app.get("/health")
def health():
    return {"status": "ok"}
