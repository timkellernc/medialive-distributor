"""Main application entry point."""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import socketio
from app.config import settings
from app.database import init_db
from app.services.ffmpeg_service import ffmpeg_service
from app.api import inputs, outputs, system
import uvicorn

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/app.log')
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Stream Distribution Manager...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)
    
    # Start background tasks here if needed
    logger.info("Application started successfully")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down...")
    await ffmpeg_service.cleanup()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.cors_origins,
    ping_interval=settings.websocket_ping_interval,
    ping_timeout=settings.websocket_ping_timeout
)

# Wrap with ASGI app
socket_app = socketio.ASGIApp(sio, app)

# Include routers
app.include_router(inputs.router, prefix="/api/inputs", tags=["inputs"])
app.include_router(outputs.router, prefix="/api/inputs", tags=["outputs"])
app.include_router(system.router, prefix="/api/system", tags=["system"])

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
except Exception as e:
    logger.warning(f"Static files directory not found: {e}")


@app.get("/")
async def read_root():
    """Serve the main application page."""
    try:
        return FileResponse("app/static/index.html")
    except:
        return {"message": "Stream Distribution Manager API", "version": settings.app_version}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version
    }


# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    """Handle client connection."""
    logger.info(f"Client connected: {sid}")


@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {sid}")


@sio.event
async def subscribe_input(sid, data):
    """Subscribe to input updates."""
    input_id = data.get('input_id')
    await sio.enter_room(sid, f"input_{input_id}")
    logger.info(f"Client {sid} subscribed to input {input_id}")


@sio.event
async def unsubscribe_input(sid, data):
    """Unsubscribe from input updates."""
    input_id = data.get('input_id')
    await sio.leave_room(sid, f"input_{input_id}")
    logger.info(f"Client {sid} unsubscribed from input {input_id}")


async def broadcast_input_status(input_id: int, status: str, stats: dict):
    """Broadcast input status update to subscribed clients."""
    await sio.emit(
        'input_status_update',
        {
            'input_id': input_id,
            'status': status,
            'stats': stats
        },
        room=f"input_{input_id}"
    )


async def broadcast_output_status(input_id: int, output_id: int, status: str, stats: dict):
    """Broadcast output status update to subscribed clients."""
    await sio.emit(
        'output_status_update',
        {
            'input_id': input_id,
            'output_id': output_id,
            'status': status,
            'stats': stats
        },
        room=f"input_{input_id}"
    )


async def broadcast_system_alert(alert_type: str, message: str):
    """Broadcast system alert to all clients."""
    await sio.emit(
        'system_alert',
        {
            'type': alert_type,
            'message': message
        }
    )


# Make broadcast functions available globally
app.state.broadcast_input_status = broadcast_input_status
app.state.broadcast_output_status = broadcast_output_status
app.state.broadcast_system_alert = broadcast_system_alert


if __name__ == "__main__":
    import os
    os.makedirs("logs", exist_ok=True)
    
    uvicorn.run(
        socket_app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower()
    )
