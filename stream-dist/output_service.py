"""Output service for managing output streams."""

import asyncio
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Input, Output, OutputStatus, Log, LogLevel
from app.schemas import OutputCreate, OutputUpdate
from app.services.ffmpeg_service import ffmpeg_service
from app.services.mediamtx_service import mediamtx_service
from app.config import settings

logger = logging.getLogger(__name__)


class OutputService:
    """Service for managing output streams."""

    @staticmethod
    async def create_output(db: Session, input_id: int, output_data: OutputCreate) -> Output:
        """Create a new output for an input."""
        try:
            # Verify input exists
            input_obj = db.query(Input).filter(Input.id == input_id).first()
            if not input_obj:
                raise ValueError(f"Input {input_id} not found")

            # Check output limit
            output_count = db.query(Output).filter(Output.input_id == input_id).count()
            if output_count >= settings.max_outputs_per_input:
                raise ValueError(f"Maximum {settings.max_outputs_per_input} outputs per input reached")

            # Check if output name already exists for this input
            existing = db.query(Output).filter(
                Output.input_id == input_id,
                Output.name == output_data.name
            ).first()
            if existing:
                raise ValueError(f"Output with name '{output_data.name}' already exists for this input")

            # Create output record
            new_output = Output(
                input_id=input_id,
                name=output_data.name,
                url=output_data.url,
                protocol=output_data.protocol,
                auto_reconnect=output_data.auto_reconnect,
                reconnect_delay=output_data.reconnect_delay,
                status=OutputStatus.STARTING
            )

            db.add(new_output)
            db.commit()
            db.refresh(new_output)

            # Start FFmpeg process
            input_srt_url = mediamtx_service.get_srt_url(input_obj.mediamtx_path, input_obj.srt_port)
            success = await ffmpeg_service.start_output(
                new_output.id,
                input_srt_url,
                output_data.url,
                output_data.protocol
            )

            if success:
                new_output.status = OutputStatus.RUNNING
            else:
                new_output.status = OutputStatus.ERROR
                new_output.last_error = "Failed to start FFmpeg process"

            db.commit()
            db.refresh(new_output)

            # Log creation
            log = Log(
                entity_type='output',
                entity_id=new_output.id,
                input_id=input_id,
                output_id=new_output.id,
                level=LogLevel.INFO,
                message=f"Output '{output_data.name}' created with protocol {output_data.protocol}"
            )
            db.add(log)
            db.commit()

            logger.info(f"Created output {new_output.id} for input {input_id}")
            return new_output

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create output: {e}")
            raise

    @staticmethod
    def get_output(db: Session, output_id: int) -> Optional[Output]:
        """Get output by ID."""
        return db.query(Output).filter(Output.id == output_id).first()

    @staticmethod
    def list_outputs(db: Session, input_id: int) -> List[Output]:
        """List all outputs for an input."""
        return db.query(Output).filter(Output.input_id == input_id).all()

    @staticmethod
    async def update_output(db: Session, output_id: int, output_data: OutputUpdate) -> Optional[Output]:
        """Update an output."""
        try:
            output_obj = db.query(Output).filter(Output.id == output_id).first()
            if not output_obj:
                return None

            needs_restart = False

            # Update fields
            if output_data.name:
                # Check if new name already exists for this input
                existing = db.query(Output).filter(
                    Output.input_id == output_obj.input_id,
                    Output.name == output_data.name,
                    Output.id != output_id
                ).first()
                if existing:
                    raise ValueError(f"Output with name '{output_data.name}' already exists for this input")
                
                output_obj.name = output_data.name

            if output_data.url:
                output_obj.url = output_data.url
                needs_restart = True

            if output_data.auto_reconnect is not None:
                output_obj.auto_reconnect = output_data.auto_reconnect

            if output_data.reconnect_delay:
                output_obj.reconnect_delay = output_data.reconnect_delay

            db.commit()
            db.refresh(output_obj)

            # Restart if URL changed and output is running
            if needs_restart and output_obj.status == OutputStatus.RUNNING:
                await OutputService.restart_output(db, output_id)

            logger.info(f"Updated output {output_id}")
            return output_obj

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update output {output_id}: {e}")
            raise

    @staticmethod
    async def delete_output(db: Session, output_id: int) -> bool:
        """Delete an output."""
        try:
            output_obj = db.query(Output).filter(Output.id == output_id).first()
            if not output_obj:
                return False

            # Stop FFmpeg process
            await ffmpeg_service.stop_output(output_id)

            # Delete from database
            db.delete(output_obj)
            db.commit()

            logger.info(f"Deleted output {output_id}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete output {output_id}: {e}")
            raise

    @staticmethod
    async def start_output(db: Session, output_id: int) -> bool:
        """Start an output."""
        try:
            output_obj = db.query(Output).filter(Output.id == output_id).first()
            if not output_obj:
                return False

            if output_obj.status == OutputStatus.RUNNING:
                logger.warning(f"Output {output_id} is already running")
                return True

            # Get input for SRT URL
            input_obj = db.query(Input).filter(Input.id == output_obj.input_id).first()
            if not input_obj:
                raise ValueError(f"Input {output_obj.input_id} not found")

            # Update status
            output_obj.status = OutputStatus.STARTING
            db.commit()

            # Start FFmpeg
            input_srt_url = mediamtx_service.get_srt_url(input_obj.mediamtx_path, input_obj.srt_port)
            success = await ffmpeg_service.start_output(
                output_id,
                input_srt_url,
                output_obj.url,
                output_obj.protocol
            )

            if success:
                output_obj.status = OutputStatus.RUNNING
                output_obj.last_error = None
            else:
                output_obj.status = OutputStatus.ERROR
                output_obj.last_error = "Failed to start FFmpeg process"

            db.commit()
            
            # Log start
            log = Log(
                entity_type='output',
                entity_id=output_id,
                input_id=output_obj.input_id,
                output_id=output_id,
                level=LogLevel.INFO,
                message=f"Output '{output_obj.name}' started"
            )
            db.add(log)
            db.commit()

            logger.info(f"Started output {output_id}")
            return success

        except Exception as e:
            logger.error(f"Failed to start output {output_id}: {e}")
            if output_obj:
                output_obj.status = OutputStatus.ERROR
                output_obj.last_error = str(e)
                db.commit()
            raise

    @staticmethod
    async def stop_output(db: Session, output_id: int) -> bool:
        """Stop an output."""
        try:
            output_obj = db.query(Output).filter(Output.id == output_id).first()
            if not output_obj:
                return False

            if output_obj.status == OutputStatus.STOPPED:
                logger.warning(f"Output {output_id} is already stopped")
                return True

            # Stop FFmpeg
            await ffmpeg_service.stop_output(output_id)

            # Update status
            output_obj.status = OutputStatus.STOPPED
            output_obj.process_id = None
            db.commit()

            # Log stop
            log = Log(
                entity_type='output',
                entity_id=output_id,
                input_id=output_obj.input_id,
                output_id=output_id,
                level=LogLevel.INFO,
                message=f"Output '{output_obj.name}' stopped"
            )
            db.add(log)
            db.commit()

            logger.info(f"Stopped output {output_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to stop output {output_id}: {e}")
            raise

    @staticmethod
    async def restart_output(db: Session, output_id: int) -> bool:
        """Restart an output."""
        await OutputService.stop_output(db, output_id)
        await asyncio.sleep(1)
        return await OutputService.start_output(db, output_id)

    @staticmethod
    def get_output_stats(db: Session, output_id: int) -> dict:
        """Get statistics for an output."""
        output_obj = db.query(Output).filter(Output.id == output_id).first()
        if not output_obj:
            return {}

        stats = ffmpeg_service.get_output_stats(output_id) or {}
        
        return {
            'id': output_obj.id,
            'name': output_obj.name,
            'status': output_obj.status,
            'reconnect_count': output_obj.reconnect_count,
            'last_error': output_obj.last_error,
            'process_stats': stats,
            'created_at': output_obj.created_at,
        }

    @staticmethod
    def get_output_logs(db: Session, output_id: int, limit: int = 100) -> List[Log]:
        """Get logs for an output."""
        return db.query(Log).filter(
            Log.output_id == output_id
        ).order_by(Log.timestamp.desc()).limit(limit).all()


# Singleton instance
output_service = OutputService()
