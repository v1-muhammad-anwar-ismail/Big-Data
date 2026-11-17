from fastapi import APIRouter
from app.config import settings
from app.database import check_db_health

router = APIRouter(prefix="/api", tags=["System Status"])

@router.get("/health")
def health_check():
    db_status = check_db_health()
    return {
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "backend_port": settings.PORT,
        "frontend_port": 5001,
        "backend_domain": settings.BACKEND_DOMAIN.replace("https://", "").replace("http://", "").rstrip("/"),
        "frontend_domain": settings.FRONTEND_DOMAIN.replace("https://", "").replace("http://", "").rstrip("/"),
        "cors_origins": settings.CORS_ORIGINS,
        "database": db_status
    }
