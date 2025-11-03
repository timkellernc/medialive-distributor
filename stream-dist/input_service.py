"""Input service for managing input streams."""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Input, Output, StreamStatus, OutputStatus, Log, LogLevel
from app.schemas import InputCreate, InputUpdate
from app.services.mediamtx_service import mediamtx_service
from app.services.ffmpeg_service import ffmpeg_service
from app.config import settings

logger = logging.getLogger(__name__)


class InputService:
    """Service for managing input streams."""

    @staticmethod
    def _find_available_udp_port(db: Session, requested_port: Optional[int] = None) -> int:
        """Find an available UDP port."""
        if requested_port:
            # Check if requested port is available
            existing = db.query(Input).filter(Input.udp_port == requested_port).first()
            if not existing:
                if settings.udp_port_range_start <= requested_port <= settings.udp_port_range_end:
                    return requested_port
                else:
                    raise ValueError(f"Port {requested_port} is outside allowed range")
            else:
                raise ValueError(f"Port {requested_port} is already in use")

        # Auto-assign port
        used_ports = {inp.udp_port for inp in db.query(Input.udp_port).all()}
        
        for port in range(settings.udp_port_range_start, settings.udp_port_range_end + 1):
            if port not in used_ports:
                return port
        
        raise ValueError("No available UDP ports in configured range")

    @staticmethod
    def _find_available_srt_port(db: Session) -> int:
        """Find an available SRT port."""
        used_ports = {inp.srt_port for inp in db.query(Input.srt_port).all()}
        
        for port in range(settings.srt_port_range_start, settings.srt_port_range_end + 1):
            if port not in used_ports:
                return port
        
        raise ValueError("No available SRT ports in configured range")

    @staticmethod
    def _generate_mediamtx_path(name: str, db: Session) -> str:
        """Generate unique MediaMTX path name."""
        # Clean name and make it URL-safe
        base_path = name.lower().replace(' ', '_').replace('-', '_')
        base_path = ''.join(c for c in base_path if c.isalnum() or c == '_')
        
        # Ensure uniqueness
        path = base_path
        counter = 1
        while db.query(Input).filter(Input.mediamtx_path == path).first():
            path = f"{base_path}_{counter}"
            counter += 1
        
        return path

    @staticmethod
    async def create_input(db: Session, input_data: InputCreate) -> Input:
        """Create a new input stream."""
        try:
            # Check if name already exists
            existing = db.query(Input).filter(Input.name == input_data.name).first()
            if existing:
                raise ValueError(f"Input with name '{input_data.name}' already exists")

            # Assign ports
            udp_port = InputService._find_available_udp_port(db, input_data.udp_port)
            srt_port = InputService._find_available_srt_port(db)
            mediamtx_path = InputService._generate_mediamtx_path(input_data.name, db)

            # Create input record
            new_input = Input(
                name=input_data.name,
                udp_port=udp_port,
                srt_port=srt_port,
                mediamtx_path=mediamtx_path,
                status=StreamStatus.INACTIVE
            )

            db.add(new_input)
            db.commit()
            db.refresh(new_input)

            # Configure MediaMTX
            success = mediamtx_service.add_input_path(mediamtx_path, udp_port, srt_port)
            if not success:
                logger.error(f"Failed to configure MediaMTX for input {new_input.id}")
                # Don't rollback, user can retry or fix manually

            # Log creation
            log = Log(
                entity_type='input',
                entity_id=new_input.id,
                input_id=new_input.id,
                level=LogLevel.INFO,
                message=f"Input '{input_data.name}' created on UDP port {udp_port}"
            )
            db.add(log)
            db.commit()

            logger.info(f"Created input {new_input.id}: {input_data.name}")
            return new_input

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create input: {e}")
            raise

    @staticmethod
    def get_input(db: Session, input_id: int) -> Optional[Input]:
        """Get input by ID."""
        return db.query(Input).filter(Input.id == input_id).first()

    @staticmethod
    def get_input_by_name(db: Session, name: str) -> Optional[Input]:
        """Get input by name."""
        return db.query(Input).filter(Input.name == name).first()

    @staticmethod
    def list_inputs(db: Session, skip: int = 0, limit: int = 100) -> List[Input]:
        """List all inputs with pagination."""
        return db.query(Input).offset(skip).limit(limit).all()

    @staticmethod
    async def update_input(db: Session, input_id: int, input_data: InputUpdate) -> Optional[Input]:
        """Update an input."""
        try:
            input_obj = db.query(Input).filter(Input.id == input_id).first()
            if not input_obj:
                return None

            # Update name if provided
            if input_data.name:
                # Check if new name already exists
                existing = db.query(Input).filter(
                    Input.name == input_data.name,
                    Input.id != input_id
                ).first()
                if existing:
                    raise ValueError(f"Input with name '{input_data.name}' already exists")
                
                input_obj.name = input_data.name

            db.commit()
            db.refresh(input_obj)

            logger.info(f"Updated input {input_id}")
            return input_obj

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update input {input_id}: {e}")
            raise

    @staticmethod
    async def delete_input(db: Session, input_id: int) -> bool:
        """Delete an input and all its outputs."""
        try:
            input_obj = db.query(Input).filter(Input.id == input_id).first()
            if not input_obj:
                return False

            # Stop all outputs
            outputs = db.query(Output).filter(Output.input_id == input_id).all()
            for output in outputs:
                await ffmpeg_service.stop_output(output.id)

            # Remove from MediaMTX
            mediamtx_service.remove_input_path(input_obj.mediamtx_path)

            # Delete from database (cascade will delete outputs and logs)
            db.delete(input_obj)
            db.commit()

            logger.info(f"Deleted input {input_id}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete input {input_id}: {e}")
            raise

    @staticmethod
    def get_input_stats(db: Session, input_id: int) -> dict:
        """Get statistics for an input."""
        input_obj = db.query(Input).filter(Input.id == input_id).first()
        if not input_obj:
            return {}

        output_count = db.query(func.count(Output.id)).filter(Output.input_id == input_id).scalar()
        
        active_outputs = db.query(func.count(Output.id)).filter(
            Output.input_id == input_id,
            Output.status == OutputStatus.RUNNING
        ).scalar()

        return {
            'id': input_obj.id,
            'name': input_obj.name,
            'status': input_obj.status,
            'udp_port': input_obj.udp_port,
            'srt_port': input_obj.srt_port,
            'output_count': output_count,
            'active_outputs': active_outputs,
            'created_at': input_obj.created_at,
        }


# Singleton instance
input_service = InputService()
