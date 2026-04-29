from fastapi import APIRouter

from app.api.v1.routers import assets

api_router = APIRouter()
from app.api.v1.routers import assets, auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
