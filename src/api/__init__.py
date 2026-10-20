"""FastAPI application package."""

from src.api.main import app
from src.api.routes import router

__all__ = ["app", "router"]
