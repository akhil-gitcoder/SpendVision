from fastapi import APIRouter

from app.api import health, transactions, analytics, ai, anomalies, auth, uploads

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(uploads.router, prefix="/transactions/uploads", tags=["uploads"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(anomalies.router, prefix="/anomalies", tags=["anomalies"])