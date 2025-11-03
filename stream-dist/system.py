"""API routes for system management."""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import SystemStatus, MediaMTXStatus, SuccessResponse
from app.services.mediamtx_service import mediamtx_service
from app.config import settings
from app.models import Input, Output, OutputStatus
from sqlalchemy import func
import psutil
import time
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Track application start time
start_time = time.time()


def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key."""
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


@router.get("/status", response_model=SystemStatus)
async def get_system_status(
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key)
):
    """Get system status and statistics."""
    try:
        # Get counts
        inputs_count = db.query(func.count(Input.id)).scalar()
        outputs_count = db.query(func.count(Output.id)).scalar()
        active_outputs = db.query(func.count(Output.id)).filter(
            Output.status == OutputStatus.RUNNING
        ).scalar()
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Check MediaMTX health
        mediamtx_healthy = await mediamtx_service.check_health()
        
        # Calculate uptime
        uptime_seconds = int(time.time() - start_time)
        
        return {
            "healthy": True,
            "version": settings.app_version,
            "uptime_seconds": uptime_seconds,
            "inputs_count": inputs_count,
            "outputs_count": outputs_count,
            "active_outputs": active_outputs,
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "mediamtx_healthy": mediamtx_healthy
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/mediamtx/status", response_model=MediaMTXStatus)
async def get_mediamtx_status(_api_key: str = Depends(verify_api_key)):
    """Get MediaMTX status."""
    try:
        healthy = await mediamtx_service.check_health()
        paths = await mediamtx_service.get_paths() if healthy else []
        
        return {
            "healthy": healthy,
            "api_available": healthy,
            "paths_count": len(paths)
        }
    except Exception as e:
        logger.error(f"Error getting MediaMTX status: {e}")
        return {
            "healthy": False,
            "api_available": False,
            "paths_count": 0
        }


@router.post("/mediamtx/restart", response_model=SuccessResponse)
async def restart_mediamtx(_api_key: str = Depends(verify_api_key)):
    """Restart MediaMTX (requires container restart)."""
    return {
        "success": False,
        "message": "MediaMTX restart must be done via Docker: docker restart stream-manager-mediamtx"
    }
