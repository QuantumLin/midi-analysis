"""Aggregates all API route modules under a single router."""

from fastapi import APIRouter

from app.api.routes import analysis, health, videos

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(analysis.router)
api_router.include_router(videos.router)
