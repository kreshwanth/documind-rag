from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.config import settings
import logging

router = APIRouter()
logger = logging.getLogger("documind.health")

@router.get("/health", status_code=status.HTTP_200_OK)
def get_health(db: Session = Depends(get_db)):
    """
    Health check endpoint returning API status, database connectivity, and pgvector availability.
    """
    res = {
        "status": "healthy",
        "database": "disconnected",
        "vector_extension": "unavailable"
    }

    try:
        db.execute(text("SELECT 1;"))
        res["database"] = "connected"
    except Exception as e:
        logger.error(f"Database connectivity check failed: {e}")
        res["status"] = "degraded"
        return res

    # Vector check
    if settings.DATABASE_URL.startswith("sqlite"):
        res["vector_extension"] = "available"
    else:
        try:
            ext_check = db.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'vector';")).fetchone()
            if ext_check:
                res["vector_extension"] = "available"
            else:
                res["status"] = "degraded"
        except Exception as e:
            logger.error(f"pgvector check failed: {e}")
            res["status"] = "degraded"

    return res
