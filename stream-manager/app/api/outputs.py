"""API routes for output management."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import OutputCreate, OutputUpdate, OutputResponse, SuccessResponse
from app.services.output_service import output_service
from app.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key."""
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


@router.post("/{input_id}/outputs", response_model=OutputResponse, status_code=201)
async def create_output(
    input_id: int,
    output_data: OutputCreate,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key)
):
    """Create a new output for an input."""
    try:
        new_output = await output_service.create_output(db, input_id, output_data)
        return new_output
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating output: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{input_id}/outputs", response_model=List[OutputResponse])
async def list_outputs(
    input_id: int,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key)
):
    """List all outputs for an input."""
    outputs = output_service.list_outputs(db, input_id)
    return outputs


@router.get("/{input_id}/outputs/{output_id}", response_model=OutputResponse)
async def get_output(
    input_id: int,
    output_id: int,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key)
):
    """Get output details."""
    output_obj = output_service.get_output(db, output_id)
    if not output_obj or output_obj.input_id != input_id:
        raise HTTPException(status_code=404, detail="Output not found")
    return output_obj


@router.patch("/{input_id}/outputs/{output_id}", response_model=OutputResponse)
async def update_output(
    input_id: int,
    output_id: int,
    output_data: OutputUpdate,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key)
):
    """Update an output."""
    try:
        updated_output = await output_service.update_output(db, output_id, output_data)
        if not updated_output or updated_output.input_id != input_id:
            raise HTTPException(status_code=404, detail="Output not found")
        return updated_output
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating output: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{input_id}/outputs/{output_id}", response_model=SuccessResponse)
async def delete_output(
    input_id: int,
    output_id: int,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key)
):
    """Delete an output."""
    try:
        success = await output_service.delete_output(db, output_id)
        if not success:
            raise HTTPException(status_code=404, detail="Output not found")
        return {"success": True, "message": f"Output {output_id} deleted"}
    except Exception as e:
        logger.error(f"Error deleting output: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{input_id}/outputs/{output_id}/start", response_model=SuccessResponse)
async def start_output(
    input_id: int,
    output_id: int,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key)
):
    """Start an output."""
    try:
        success = await output_service.start_output(db, output_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to start output")
        return {"success": True, "message": f"Output {output_id} started"}
    except Exception as e:
        logger.error(f"Error starting output: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{input_id}/outputs/{output_id}/stop", response_model=SuccessResponse)
async def stop_output(
    input_id: int,
    output_id: int,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key)
):
    """Stop an output."""
    try:
        success = await output_service.stop_output(db, output_id)
        if not success:
            raise HTTPException(status_code=404, detail="Output not found")
        return {"success": True, "message": f"Output {output_id} stopped"}
    except Exception as e:
        logger.error(f"Error stopping output: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{input_id}/outputs/{output_id}/logs")
async def get_output_logs(
    input_id: int,
    output_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key)
):
    """Get logs for an output."""
    logs = output_service.get_output_logs(db, output_id, limit)
    return logs
