from fastapi import APIRouter

from app.api.v1 import admin, auth, brands, catalogs, jobs, products, public

api_router = APIRouter(prefix="/api/v1")
for r in (auth, brands, catalogs, products, jobs, public, admin):
    api_router.include_router(r.router)
