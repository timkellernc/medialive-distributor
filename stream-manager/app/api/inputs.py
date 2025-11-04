"""API routes for input management."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    InputCreate, InputUpdate, InputResponse, InputDetail,
    ErrorResponse, SuccessResponse
)
from app.services.input_service import input_service
from app.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key."""
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


@router.post("/", response_model=InputResponse, status_code=201)
async def create_input(
    input_data: InputCreate,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key)
):
    """Create a new input stream."""
    try:
        new_input = await input_service.create_input(db, input_data)
        return new_input
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating input: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=List[InputResponse])
async def list_inputs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key)
):
    """List all inputs."""
    inputs = input_service.list_inputs(db, skip, limit)
    
    # Add output count to each input
    result = []
    for inp in inputs:
        inp_dict = {
            'id': inp.id,
            'name': inp.name,
            'udp_port': inp.udp_port,
            'mediamtx_path': inp.mediamtx_path,
            'srt_port': inp.srt_port,
            'status': inp.status,
            'created_at': inp.created_at,
            'updated_at': inp.updated_at,
            'output_count': len(inp.outputs)
        }
        result.append(inp_dict)
    
    return result


@router.get("/{input_id}", response_model=InputDetail)
async def get_input(
    input_id: int,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key)
):
    """Get input details including all outputs."""
    input_obj = input_service.get_input(db, input_id)
    if not input_obj:
        raise HTTPException(status_code=404, detail="Input not found")
    
    return input_obj


@router.patch("/{input_id}", response_model=InputResponse)
async def update_input(
    input_id: int,
    input_data: InputUpdate,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key)
):
    """Update an input."""
    try:
        updated_input = await input_service.update_input(db, input_id, input_data)
        if not updated_input:
            raise HTTPException(status_code=404, detail="Input not found")
        return updated_input
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating input: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{input_id}", response_model=SuccessResponse)
async def delete_input(
    input_id: int,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key)
):
    """Delete an input and all its outputs."""
    try:
        success = await input_service.delete_input(db, input_id)
        if not success:
            raise HTTPException(status_code=404, detail="Input not found")
        return {"success": True, "message": f"Input {input_id} deleted"}
    except Exception as e:
        logger.error(f"Error deleting input: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{input_id}/status")
async def get_input_status(
    input_id: int,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key)
):
    """Get input status and statistics."""
    stats = input_service.get_input_stats(db, input_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Input not found")
    return stats
