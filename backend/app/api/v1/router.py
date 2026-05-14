from fastapi import APIRouter

from app.api.v1.endpoints import ab_tests, products, scripts, streams

api_router = APIRouter()
api_router.include_router(streams.router, prefix="/streams", tags=["streams"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(scripts.router, prefix="/scripts", tags=["scripts"])
api_router.include_router(ab_tests.router, prefix="/ab-tests", tags=["ab-tests"])
