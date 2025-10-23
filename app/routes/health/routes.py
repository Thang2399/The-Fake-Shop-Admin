from fastapi import APIRouter
from app.db import db

router = APIRouter(prefix="/admin/health", tags=["Health"])

@router.get("/")
async def health_check():
    try:
        # Run a simple ping or query
        await db.command("ping")
        return {"status": "connected"}
    except Exception as e:
        return {"status": "error", "details": str(e)}