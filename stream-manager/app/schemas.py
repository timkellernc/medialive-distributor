"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.models import StreamStatus, OutputStatus, ProtocolType, LogLevel


# Input Schemas
class InputBase(BaseModel):
    """Base input schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Input stream name")
    udp_port: Optional[int] = Field(None, ge=1024, le=65535, description="UDP port number")


class InputCreate(InputBase):
    """Schema for creating an input."""
    pass


class InputUpdate(BaseModel):
    """Schema for updating an input."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class InputResponse(InputBase):
    """Schema for input response."""
    id: int
    mediamtx_path: str
    srt_port: int
    status: StreamStatus
    created_at: datetime
    updated_at: datetime
    output_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class InputDetail(InputResponse):
    """Detailed input schema with outputs."""
    outputs: List['OutputResponse'] = []


# Output Schemas
class OutputBase(BaseModel):
    """Base output schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Output name")
    url: str = Field(..., min_length=1, max_length=1024, description="Destination URL")
    protocol: ProtocolType = Field(..., description="Protocol type")
    auto_reconnect: bool = Field(True, description="Enable auto-reconnect")
    reconnect_delay: int = Field(5, ge=1, le=300, description="Reconnect delay in seconds")

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str, info) -> str:
        """Validate URL format based on protocol."""
        protocol = info.data.get('protocol')
        
        if protocol == ProtocolType.SRT_CALLER:
            if not v.startswith('srt://'):
                raise ValueError("SRT caller URL must start with srt://")
        elif protocol == ProtocolType.SRT_LISTENER:
            if not v.startswith('srt://'):
                raise ValueError("SRT listener URL must start with srt://")
        elif protocol == ProtocolType.RTMP:
            if not v.startswith('rtmp://') and not v.startswith('rtmps://'):
                raise ValueError("RTMP URL must start with rtmp:// or rtmps://")
        elif protocol == ProtocolType.UDP:
            if not v.startswith('udp://'):
                raise ValueError("UDP URL must start with udp://")
        elif protocol == ProtocolType.RTSP:
            if not v.startswith('rtsp://'):
                raise ValueError("RTSP URL must start with rtsp://")
        
        return v


class OutputCreate(OutputBase):
    """Schema for creating an output."""
    pass


class OutputUpdate(BaseModel):
    """Schema for updating an output."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = Field(None, min_length=1, max_length=1024)
    auto_reconnect: Optional[bool] = None
    reconnect_delay: Optional[int] = Field(None, ge=1, le=300)


class OutputResponse(OutputBase):
    """Schema for output response."""
    id: int
    input_id: int
    status: OutputStatus
    reconnect_count: int
    last_error: Optional[str] = None
    process_id: Optional[int] = None
    started_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OutputStats(BaseModel):
    """Output statistics."""
    uptime_seconds: Optional[int] = None
    reconnect_count: int
    last_error: Optional[str] = None
    status: OutputStatus


# Log Schemas
class LogCreate(BaseModel):
    """Schema for creating a log entry."""
    entity_type: str
    entity_id: Optional[int] = None
    input_id: Optional[int] = None
    output_id: Optional[int] = None
    level: LogLevel
    message: str


class LogResponse(BaseModel):
    """Schema for log response."""
    id: int
    entity_type: str
    entity_id: Optional[int] = None
    level: LogLevel
    message: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class LogFilter(BaseModel):
    """Schema for log filtering."""
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    level: Optional[LogLevel] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


# System Schemas
class SystemStatus(BaseModel):
    """System status response."""
    healthy: bool
    version: str
    uptime_seconds: int
    inputs_count: int
    outputs_count: int
    active_outputs: int
    cpu_percent: float
    memory_percent: float
    mediamtx_healthy: bool


class MediaMTXStatus(BaseModel):
    """MediaMTX status response."""
    healthy: bool
    api_available: bool
    paths_count: int


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None


class SuccessResponse(BaseModel):
    """Success response schema."""
    success: bool
    message: str
    data: Optional[dict] = None


# WebSocket Messages
class WSMessage(BaseModel):
    """WebSocket message schema."""
    event: str
    data: dict


class WSInputStatusUpdate(BaseModel):
    """WebSocket input status update."""
    input_id: int
    status: StreamStatus
    output_count: int


class WSOutputStatusUpdate(BaseModel):
    """WebSocket output status update."""
    input_id: int
    output_id: int
    status: OutputStatus
    reconnect_count: int
    last_error: Optional[str] = None


class WSSystemAlert(BaseModel):
    """WebSocket system alert."""
    type: str  # 'info', 'warning', 'error'
    message: str
    timestamp: datetime


# Update forward references
InputDetail.model_rebuild()
