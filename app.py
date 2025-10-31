"""
MediaLive Distributor - Production Grade Stream Distribution
Receives RTP streams from AWS MediaLive and distributes to multiple SRT/RTMP outputs
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG_DIR = Path(os.getenv("CONFIG_DIR", "/app/config"))
CONFIG_FILE = CONFIG_DIR / "channels.json"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Global state
channels: Dict[str, 'Channel'] = {}
websocket_clients: List[WebSocket] = []


# Pydantic Models
class OutputConfig(BaseModel):
    name: str = Field(..., description="Output name")
    protocol: str = Field(..., pattern="^(srt|rtmp)$", description="Output protocol")
    url: str = Field(..., description="Output URL")
    enabled: bool = Field(default=True, description="Enable/disable output")


class OutputCreate(BaseModel):
    name: Optional[str] = Field(None, description="Output name (auto-generated if not provided)")
    protocol: str = Field(..., pattern="^(srt|rtmp)$", description="Output protocol (srt or rtmp)")
    url: str = Field(..., description="Output URL")


class ChannelConfig(BaseModel):
    name: str = Field(..., description="Channel name")
    rtp_ip: str = Field(..., description="RTP input IP address")
    rtp_port: int = Field(..., ge=1024, le=65535, description="RTP input port")
    backup_rtp_ip: Optional[str] = Field(None, description="Backup RTP IP (optional)")
    backup_rtp_port: Optional[int] = Field(None, ge=1024, le=65535, description="Backup RTP port (optional)")
    outputs: List[OutputConfig] = Field(default_factory=list, description="Output configurations")


class ChannelStatus(BaseModel):
    id: str
    name: str
    rtp_ip: str
    rtp_port: int
    backup_rtp_ip: Optional[str]
    backup_rtp_port: Optional[int]
    status: str
    uptime: Optional[float]
    outputs: List[dict]
    created_at: str
    started_at: Optional[str]


class Output:
    """Represents a single output stream (SRT or RTMP)"""
    
    def __init__(self, output_id: str, config: OutputConfig, channel_id: str):
        self.id = output_id
        self.config = config
        self.channel_id = channel_id
        self.process: Optional[subprocess.Popen] = None
        self.status = "stopped"
        self.started_at: Optional[float] = None
        self.error_count = 0
        self.last_error: Optional[str] = None
        
    def get_ffmpeg_command(self, input_url: str) -> List[str]:
        """Generate FFmpeg command for this output"""
        cmd = [
            "ffmpeg",
            "-loglevel", "warning",
            "-i", input_url,
            "-c", "copy",  # No transcoding
            "-copyts",  # Preserve timestamps
        ]
        
        if self.config.protocol == "srt":
            # SRT output with SCTE-35 preservation
            cmd.extend([
                "-f", "mpegts",
                "-mpegts_flags", "initial_discontinuity",
                "-muxdelay", "0",
                self.config.url
            ])
        else:  # RTMP
            cmd.extend([
                "-f", "flv",
                self.config.url
            ])
        
        return cmd
    
    async def start(self, input_url: str):
        """Start the output stream"""
        if self.process and self.process.poll() is None:
            logger.warning(f"Output {self.id} already running")
            return
        
        try:
            cmd = self.get_ffmpeg_command(input_url)
            logger.info(f"Starting output {self.id}: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            self.status = "running"
            self.started_at = time.time()
            self.error_count = 0
            self.last_error = None
            
            # Start monitoring in background
            asyncio.create_task(self._monitor_process())
            
            logger.info(f"Output {self.id} started successfully")
            
        except Exception as e:
            self.status = "error"
            self.last_error = str(e)
            self.error_count += 1
            logger.error(f"Failed to start output {self.id}: {e}")
            raise
    
    async def _monitor_process(self):
        """Monitor the FFmpeg process"""
        while self.process and self.process.poll() is None:
            await asyncio.sleep(1)
        
        # Process ended
        if self.process:
            return_code = self.process.returncode
            if return_code != 0:
                stderr = self.process.stderr.read().decode() if self.process.stderr else ""
                self.last_error = f"Process exited with code {return_code}: {stderr[:200]}"
                self.error_count += 1
                self.status = "error"
                logger.error(f"Output {self.id} failed: {self.last_error}")
            else:
                self.status = "stopped"
    
    async def stop(self):
        """Stop the output stream"""
        if self.process and self.process.poll() is None:
            try:
                if os.name != 'nt':
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                else:
                    self.process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    if os.name != 'nt':
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    else:
                        self.process.kill()
                
                logger.info(f"Output {self.id} stopped")
            except Exception as e:
                logger.error(f"Error stopping output {self.id}: {e}")
        
        self.status = "stopped"
        self.process = None
        self.started_at = None
    
    def get_status(self) -> dict:
        """Get output status"""
        uptime = time.time() - self.started_at if self.started_at else None
        
        return {
            "id": self.id,
            "name": self.config.name,
            "protocol": self.config.protocol,
            "url": self.config.url,
            "enabled": self.config.enabled,
            "status": self.status,
            "uptime": uptime,
            "error_count": self.error_count,
            "last_error": self.last_error
        }


class Channel:
    """Represents a MediaLive channel with multiple outputs"""
    
    def __init__(self, channel_id: str, config: ChannelConfig):
        self.id = channel_id
        self.config = config
        self.outputs: Dict[str, Output] = {}
        self.status = "stopped"
        self.created_at = datetime.utcnow().isoformat()
        self.started_at: Optional[str] = None
        self.receive_process: Optional[subprocess.Popen] = None
        self.fifo_path: Optional[str] = None
        
        # Create outputs
        for i, output_config in enumerate(config.outputs):
            output_id = f"{channel_id}-output-{i}"
            self.outputs[output_id] = Output(output_id, output_config, channel_id)
    
    def _get_rtp_url(self) -> str:
        """Get UDP/RTP input URL"""
        return f"udp://{self.config.rtp_ip}:{self.config.rtp_port}?overrun_nonfatal=1&fifo_size=50000000"
    
    def _setup_fifo(self) -> str:
        """Setup named pipe for stream distribution"""
        fifo_path = f"/tmp/channel_{self.id}.ts"
        
        # Remove existing fifo
        if os.path.exists(fifo_path):
            try:
                os.remove(fifo_path)
                logger.info(f"Removed existing FIFO: {fifo_path}")
            except Exception as e:
                logger.warning(f"Could not remove existing FIFO {fifo_path}: {e}")
        
        # Create new fifo
        try:
            os.mkfifo(fifo_path)
            logger.info(f"Created FIFO: {fifo_path}")
        except Exception as e:
            logger.error(f"Failed to create FIFO {fifo_path}: {e}")
            raise
        
        return fifo_path
    
    async def start(self):
        """Start receiving stream and all enabled outputs"""
        if self.status == "running":
            logger.warning(f"Channel {self.id} already running")
            return
        
        try:
            # Setup FIFO for stream distribution
            self.fifo_path = self._setup_fifo()
            
            # IMPORTANT: Start outputs FIRST - they will block waiting to read from FIFO
            # This allows the receiver to then open the FIFO for writing
            logger.info(f"Starting outputs for channel {self.id}")
            for output in self.outputs.values():
                if output.config.enabled:
                    try:
                        await output.start(f"file:{self.fifo_path}")
                        # Small delay between outputs
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        logger.error(f"Failed to start output {output.id}: {e}")
            
            # Give outputs time to open the FIFO for reading
            await asyncio.sleep(0.5)
            
            # Now start receiver - it can open FIFO for writing
            rtp_url = self._get_rtp_url()
            cmd = [
                "ffmpeg",
                "-loglevel", "warning",
                "-protocol_whitelist", "file,udp",
                "-i", rtp_url,
                "-c", "copy",
                "-copyts",
                "-f", "mpegts",
                "-muxdelay", "0",
                self.fifo_path
            ]
            
            logger.info(f"Starting channel {self.id} receiver: {' '.join(cmd)}")
            
            self.receive_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            # Give receiver time to start
            await asyncio.sleep(1)
            
            if self.receive_process.poll() is not None:
                stderr = self.receive_process.stderr.read().decode()
                raise Exception(f"Receiver failed to start: {stderr}")
            
            # Verify FIFO still exists
            if not os.path.exists(self.fifo_path):
                raise Exception(f"FIFO disappeared: {self.fifo_path}")
            
            logger.info(f"Receiver started and writing to FIFO: {self.fifo_path}")
            
            self.status = "running"
            self.started_at = datetime.utcnow().isoformat()
            
            logger.info(f"Channel {self.id} started successfully")
            await broadcast_status_update()
            
        except Exception as e:
            self.status = "error"
            logger.error(f"Failed to start channel {self.id}: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop channel and all outputs"""
        logger.info(f"Stopping channel {self.id}")
        
        # Stop all outputs
        for output in self.outputs.values():
            try:
                await output.stop()
            except Exception as e:
                logger.error(f"Error stopping output {output.id}: {e}")
        
        # Stop receiver
        if self.receive_process and self.receive_process.poll() is None:
            try:
                if os.name != 'nt':
                    os.killpg(os.getpgid(self.receive_process.pid), signal.SIGTERM)
                else:
                    self.receive_process.terminate()
                
                try:
                    self.receive_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    if os.name != 'nt':
                        os.killpg(os.getpgid(self.receive_process.pid), signal.SIGKILL)
                    else:
                        self.receive_process.kill()
            except Exception as e:
                logger.error(f"Error stopping receiver for channel {self.id}: {e}")
        
        # Cleanup FIFO
        if self.fifo_path and os.path.exists(self.fifo_path):
            try:
                os.remove(self.fifo_path)
            except Exception as e:
                logger.error(f"Error removing FIFO: {e}")
        
        self.status = "stopped"
        self.started_at = None
        self.receive_process = None
        self.fifo_path = None
        
        logger.info(f"Channel {self.id} stopped")
        await broadcast_status_update()
    
    async def add_output(self, output_config: OutputConfig) -> str:
        """Add a new output without interrupting existing outputs"""
        # Generate output ID
        output_id = f"{self.id}-output-{len(self.outputs)}"
        
        # Create output
        output = Output(output_id, output_config, self.id)
        self.outputs[output_id] = output
        
        # Start if channel is running and output is enabled
        if self.status == "running" and output_config.enabled and self.fifo_path:
            await output.start(f"file:{self.fifo_path}")
        
        # Save configuration
        await save_config()
        await broadcast_status_update()
        
        logger.info(f"Added output {output_id} to channel {self.id}")
        return output_id
    
    async def remove_output(self, output_id: str):
        """Remove an output"""
        if output_id not in self.outputs:
            raise ValueError(f"Output {output_id} not found")
        
        output = self.outputs[output_id]
        await output.stop()
        del self.outputs[output_id]
        
        await save_config()
        await broadcast_status_update()
        
        logger.info(f"Removed output {output_id} from channel {self.id}")
    
    async def update_output(self, output_id: str, output_config: OutputConfig):
        """Update an output configuration"""
        if output_id not in self.outputs:
            raise ValueError(f"Output {output_id} not found")
        
        output = self.outputs[output_id]
        was_running = output.status == "running"
        
        # Stop if running
        if was_running:
            await output.stop()
        
        # Update config
        output.config = output_config
        
        # Restart if was running and still enabled
        if was_running and output_config.enabled and self.status == "running" and self.fifo_path:
            await output.start(f"file:{self.fifo_path}")
        
        await save_config()
        await broadcast_status_update()
        
        logger.info(f"Updated output {output_id}")
    
    def get_status(self) -> ChannelStatus:
        """Get channel status"""
        uptime = None
        if self.started_at:
            started = datetime.fromisoformat(self.started_at)
            uptime = (datetime.utcnow() - started).total_seconds()
        
        return ChannelStatus(
            id=self.id,
            name=self.config.name,
            rtp_ip=self.config.rtp_ip,
            rtp_port=self.config.rtp_port,
            backup_rtp_ip=self.config.backup_rtp_ip,
            backup_rtp_port=self.config.backup_rtp_port,
            status=self.status,
            uptime=uptime,
            outputs=[output.get_status() for output in self.outputs.values()],
            created_at=self.created_at,
            started_at=self.started_at
        )
    
    def to_config(self) -> ChannelConfig:
        """Convert to configuration format"""
        return ChannelConfig(
            name=self.config.name,
            rtp_ip=self.config.rtp_ip,
            rtp_port=self.config.rtp_port,
            backup_rtp_ip=self.config.backup_rtp_ip,
            backup_rtp_port=self.config.backup_rtp_port,
            outputs=[output.config for output in self.outputs.values()]
        )


# Configuration persistence
async def save_config():
    """Save current configuration to disk"""
    config_data = {
        channel_id: {
            "config": channel.to_config().dict(),
            "created_at": channel.created_at
        }
        for channel_id, channel in channels.items()
    }
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    logger.debug("Configuration saved")


async def load_config():
    """Load configuration from disk"""
    if not CONFIG_FILE.exists():
        logger.info("No configuration file found, starting fresh")
        return
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config_data = json.load(f)
        
        for channel_id, data in config_data.items():
            config = ChannelConfig(**data["config"])
            channel = Channel(channel_id, config)
            channel.created_at = data.get("created_at", channel.created_at)
            channels[channel_id] = channel
        
        logger.info(f"Loaded {len(channels)} channels from configuration")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")


# WebSocket support for real-time updates
async def broadcast_status_update():
    """Broadcast status update to all connected WebSocket clients"""
    if not websocket_clients:
        return
    
    status = {
        "channels": [channel.get_status().dict() for channel in channels.values()]
    }
    
    message = json.dumps(status)
    
    disconnected = []
    for client in websocket_clients:
        try:
            await client.send_text(message)
        except:
            disconnected.append(client)
    
    # Remove disconnected clients
    for client in disconnected:
        websocket_clients.remove(client)


# FastAPI application
app = FastAPI(title="MediaLive Distributor", version="1.0.0")

# Serve static files (web dashboard)
app.mount("/static", StaticFiles(directory="/app/static"), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize application"""
    logger.info("Starting MediaLive Distributor")
    await load_config()
    logger.info("Application started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down MediaLive Distributor")
    
    for channel in channels.values():
        try:
            await channel.stop()
        except Exception as e:
            logger.error(f"Error stopping channel {channel.id}: {e}")
    
    logger.info("Shutdown complete")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve web dashboard"""
    with open("/app/static/index.html", "r") as f:
        return f.read()


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/channels")
async def list_channels():
    """List all channels"""
    return {
        "channels": [channel.get_status().dict() for channel in channels.values()]
    }


@app.post("/api/channels")
async def create_channel(config: ChannelConfig):
    """Create a new channel"""
    channel_id = str(uuid4())
    
    # Validate unique port
    for existing_channel in channels.values():
        if existing_channel.config.rtp_port == config.rtp_port:
            raise HTTPException(
                status_code=400,
                detail=f"Port {config.rtp_port} already in use by channel {existing_channel.config.name}"
            )
    
    channel = Channel(channel_id, config)
    channels[channel_id] = channel
    
    await save_config()
    await broadcast_status_update()
    
    logger.info(f"Created channel {channel_id}: {config.name}")
    
    return channel.get_status()


@app.get("/api/channels/{channel_id}")
async def get_channel(channel_id: str):
    """Get channel details"""
    if channel_id not in channels:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    return channels[channel_id].get_status()


@app.delete("/api/channels/{channel_id}")
async def delete_channel(channel_id: str):
    """Delete a channel"""
    if channel_id not in channels:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    channel = channels[channel_id]
    await channel.stop()
    del channels[channel_id]
    
    await save_config()
    await broadcast_status_update()
    
    logger.info(f"Deleted channel {channel_id}")
    
    return {"message": "Channel deleted"}


@app.post("/api/channels/{channel_id}/start")
async def start_channel(channel_id: str):
    """Start a channel"""
    if channel_id not in channels:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    try:
        await channels[channel_id].start()
        return channels[channel_id].get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/channels/{channel_id}/stop")
async def stop_channel(channel_id: str):
    """Stop a channel"""
    if channel_id not in channels:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    await channels[channel_id].stop()
    return channels[channel_id].get_status()


@app.post("/api/channels/{channel_id}/outputs")
async def add_output(channel_id: str, output: OutputCreate):
    """Add output to channel"""
    if channel_id not in channels:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Generate name if not provided
    name = output.name
    if not name:
        channel = channels[channel_id]
        name = f"Output {len(channel.outputs) + 1}"
    
    output_config = OutputConfig(
        name=name,
        protocol=output.protocol,
        url=output.url,
        enabled=True
    )
    
    try:
        output_id = await channels[channel_id].add_output(output_config)
        return {"output_id": output_id, "message": "Output added"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/channels/{channel_id}/outputs/{output_id}")
async def remove_output(channel_id: str, output_id: str):
    """Remove output from channel"""
    if channel_id not in channels:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    try:
        await channels[channel_id].remove_output(output_id)
        return {"message": "Output removed"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/channels/{channel_id}/outputs/{output_id}")
async def update_output(channel_id: str, output_id: str, output_config: OutputConfig):
    """Update output configuration"""
    if channel_id not in channels:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    try:
        await channels[channel_id].update_output(output_id, output_config)
        return {"message": "Output updated"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    websocket_clients.append(websocket)
    
    try:
        # Send initial status
        await broadcast_status_update()
        
        # Keep connection alive
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
