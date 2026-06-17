from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.core.database import ping_database

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def live() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/ready")
def ready() -> dict[str, str]:
    if not ping_database():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    return {"status": "ready"}
