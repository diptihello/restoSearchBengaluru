"""FastAPI application entry point for AI-Powered Restaurant Recommendation System."""

import logging
import time
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

from src.api.routes import router as api_router
from src.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("api")

app = FastAPI(
    title="AI-Powered Restaurant Recommendation System API",
    description=(
        "Hybrid two-stage restaurant recommendation system connecting high-speed "
        "deterministic candidate retrieval (Stage 1) with Google Gemini situational reasoning (Stage 2)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 1. CORS Middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Request Logging & Latency Tracking Middleware
@app.middleware("http")
async def add_process_time_and_log(request: Request, call_next):
    start_time = time.perf_counter()
    path = request.url.path
    method = request.method

    response = await call_next(request)

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"

    logger.info(
        "%s %s -> status=%d (took %.2f ms)",
        method,
        path,
        response.status_code,
        elapsed_ms,
    )
    return response

# 3. Custom Error Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error on %s %s: %s", request.method, request.url.path, exc.errors())
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "Invalid request parameters provided.",
            "details": exc.errors(),
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled server exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred while processing the request.",
            "detail": str(exc),
        },
    )

from src.config import BASE_DIR, settings

# 4. Mount API Routes
app.include_router(api_router)

WEB_INDEX = BASE_DIR / "frontend" / "web" / "index.html"

# 5. Root & UI endpoints
@app.get("/app", tags=["UI"], include_in_schema=False)
def serve_ui():
    """Serve the modern Google Stitch dark-theme web application."""
    if WEB_INDEX.exists():
        return FileResponse(str(WEB_INDEX))
    return {"error": "UI index file not found"}

@app.get("/", tags=["System"])
def root(request: Request):
    """Root endpoint serving Stitch UI for browsers and JSON status for API clients."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept and WEB_INDEX.exists():
        return FileResponse(str(WEB_INDEX))
    return {
        "service": "AI-Powered Restaurant Recommendation API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health",
        "options": "/api/v1/meta/options",
        "ui": "/app",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
