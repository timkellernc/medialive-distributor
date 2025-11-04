"""FFmpeg service for managing output processes."""

import asyncio
import logging
import subprocess
import psutil
from typing import Optional, Dict
from datetime import datetime
from app.config import settings
from app.models import OutputStatus, ProtocolType

logger = logging.getLogger(__name__)


class FFmpegProcess:
    """Wrapper for FFmpeg process management."""

    def __init__(self, output_id: int, input_srt_url: str, output_url: str, protocol: ProtocolType):
        self.output_id = output_id
        self.input_srt_url = input_srt_url
        self.output_url = output_url
        self.protocol = protocol
        self.process: Optional[subprocess.Popen] = None
        self.started_at: Optional[datetime] = None
        self.reconnect_count = 0
        self.should_run = False
        self.monitor_task: Optional[asyncio.Task] = None

    def build_command(self) -> list:
        """Build FFmpeg command based on output protocol."""
        base_cmd = [
            'ffmpeg',
            '-re',  # Read input at native frame rate
            '-i', self.input_srt_url,
            '-c', 'copy',  # Copy streams without re-encoding
            '-f', self._get_format(),
        ]

        # Add protocol-specific options
        if self.protocol == ProtocolType.SRT_CALLER:
            base_cmd.extend([
                '-max_delay', '5000000',  # 5 second max delay
                '-timeout', '5000000',
            ])
        elif self.protocol == ProtocolType.SRT_LISTENER:
            base_cmd.extend([
                '-max_delay', '5000000',
            ])
        elif self.protocol == ProtocolType.RTMP:
            base_cmd.extend([
                '-flvflags', 'no_duration_filesize',
            ])

        # Add output URL
        base_cmd.append(self.output_url)

        # Global options
        base_cmd.extend([
            '-loglevel', settings.ffmpeg_log_level,
            '-hide_banner',
            '-nostats',
        ])

        return base_cmd

    def _get_format(self) -> str:
        """Get FFmpeg format based on protocol."""
        format_map = {
            ProtocolType.SRT_CALLER: 'mpegts',
            ProtocolType.SRT_LISTENER: 'mpegts',
            ProtocolType.RTMP: 'flv',
            ProtocolType.UDP: 'mpegts',
            ProtocolType.RTSP: 'rtsp',
        }
        return format_map.get(self.protocol, 'mpegts')

    async def start(self) -> bool:
        """Start FFmpeg process."""
        try:
            if self.process and self.process.poll() is None:
                logger.warning(f"Output {self.output_id} already running")
                return False

            command = self.build_command()
            logger.info(f"Starting FFmpeg for output {self.output_id}: {' '.join(command)}")

            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )

            self.started_at = datetime.utcnow()
            self.should_run = True

            # Start monitoring task
            if self.monitor_task is None or self.monitor_task.done():
                self.monitor_task = asyncio.create_task(self._monitor_process())

            logger.info(f"FFmpeg started for output {self.output_id}, PID: {self.process.pid}")
            return True

        except Exception as e:
            logger.error(f"Failed to start FFmpeg for output {self.output_id}: {e}")
            return False

    async def stop(self) -> bool:
        """Stop FFmpeg process gracefully."""
        try:
            self.should_run = False

            if self.process and self.process.poll() is None:
                logger.info(f"Stopping FFmpeg for output {self.output_id}, PID: {self.process.pid}")

                # Try graceful termination first
                self.process.terminate()

                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if not terminated
                    logger.warning(f"Force killing FFmpeg for output {self.output_id}")
                    self.process.kill()
                    self.process.wait()

                logger.info(f"FFmpeg stopped for output {self.output_id}")

            # Cancel monitoring task
            if self.monitor_task and not self.monitor_task.done():
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    pass

            return True

        except Exception as e:
            logger.error(f"Failed to stop FFmpeg for output {self.output_id}: {e}")
            return False

    async def restart(self) -> bool:
        """Restart FFmpeg process."""
        await self.stop()
        await asyncio.sleep(1)
        return await self.start()

    def is_running(self) -> bool:
        """Check if process is running."""
        return self.process is not None and self.process.poll() is None

    def get_pid(self) -> Optional[int]:
        """Get process ID."""
        return self.process.pid if self.process else None

    def get_stats(self) -> Dict:
        """Get process statistics."""
        stats = {
            'running': self.is_running(),
            'pid': self.get_pid(),
            'reconnect_count': self.reconnect_count,
            'uptime_seconds': None
        }

        if self.started_at and self.is_running():
            uptime = (datetime.utcnow() - self.started_at).total_seconds()
            stats['uptime_seconds'] = int(uptime)

        if self.is_running() and self.process:
            try:
                proc = psutil.Process(self.process.pid)
                stats['cpu_percent'] = proc.cpu_percent()
                stats['memory_mb'] = proc.memory_info().rss / 1024 / 1024
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return stats

    async def _monitor_process(self):
        """Monitor process and handle failures."""
        while self.should_run:
            try:
                if not self.is_running():
                    logger.warning(f"FFmpeg process died for output {self.output_id}")
                    
                    if self.should_run:
                        # Auto-restart if configured
                        self.reconnect_count += 1
                        logger.info(f"Restarting FFmpeg for output {self.output_id} (attempt {self.reconnect_count})")
                        
                        await asyncio.sleep(settings.default_reconnect_delay)
                        await self.start()
                    else:
                        break

                await asyncio.sleep(settings.process_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring FFmpeg for output {self.output_id}: {e}")
                await asyncio.sleep(5)


class FFmpegService:
    """Service for managing multiple FFmpeg processes."""

    def __init__(self):
        self.processes: Dict[int, FFmpegProcess] = {}

    async def start_output(
        self,
        output_id: int,
        input_srt_url: str,
        output_url: str,
        protocol: ProtocolType
    ) -> bool:
        """Start FFmpeg process for an output."""
        try:
            # Stop existing process if any
            if output_id in self.processes:
                await self.stop_output(output_id)

            # Create and start new process
            process = FFmpegProcess(output_id, input_srt_url, output_url, protocol)
            success = await process.start()

            if success:
                self.processes[output_id] = process
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to start output {output_id}: {e}")
            return False

    async def stop_output(self, output_id: int) -> bool:
        """Stop FFmpeg process for an output."""
        try:
            if output_id in self.processes:
                process = self.processes[output_id]
                await process.stop()
                del self.processes[output_id]
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to stop output {output_id}: {e}")
            return False

    async def restart_output(self, output_id: int) -> bool:
        """Restart FFmpeg process for an output."""
        if output_id in self.processes:
            return await self.processes[output_id].restart()
        return False

    def get_output_status(self, output_id: int) -> OutputStatus:
        """Get status of an output."""
        if output_id not in self.processes:
            return OutputStatus.STOPPED

        process = self.processes[output_id]
        if process.is_running():
            return OutputStatus.RUNNING
        elif process.should_run:
            return OutputStatus.RECONNECTING
        else:
            return OutputStatus.STOPPED

    def get_output_stats(self, output_id: int) -> Optional[Dict]:
        """Get statistics for an output."""
        if output_id in self.processes:
            return self.processes[output_id].get_stats()
        return None

    async def stop_all_for_input(self, input_id: int, output_ids: list) -> bool:
        """Stop all outputs for an input."""
        try:
            for output_id in output_ids:
                await self.stop_output(output_id)
            return True
        except Exception as e:
            logger.error(f"Failed to stop outputs for input {input_id}: {e}")
            return False

    async def cleanup(self):
        """Stop all processes on shutdown."""
        logger.info("Cleaning up all FFmpeg processes...")
        for output_id in list(self.processes.keys()):
            await self.stop_output(output_id)
        logger.info("All FFmpeg processes stopped")


# Singleton instance
ffmpeg_service = FFmpegService()
