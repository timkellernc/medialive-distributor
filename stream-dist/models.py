"""Database models for Stream Distribution Manager."""

from datetime import datetime
from typing import List
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()


class StreamStatus(str, enum.Enum):
    """Stream status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"


class OutputStatus(str, enum.Enum):
    """Output status enum."""
    RUNNING = "running"
    STOPPED = "stopped"
    RECONNECTING = "reconnecting"
    ERROR = "error"
    STARTING = "starting"


class ProtocolType(str, enum.Enum):
    """Output protocol types."""
    SRT_CALLER = "srt_caller"
    SRT_LISTENER = "srt_listener"
    RTMP = "rtmp"
    UDP = "udp"
    RTSP = "rtsp"


class LogLevel(str, enum.Enum):
    """Log levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Input(Base):
    """Input stream model."""
    __tablename__ = "inputs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    udp_port = Column(Integer, unique=True, nullable=False)
    mediamtx_path = Column(String(255), unique=True, nullable=False)
    srt_port = Column(Integer, unique=True, nullable=False)
    status = Column(Enum(StreamStatus), default=StreamStatus.INACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    outputs = relationship("Output", back_populates="input", cascade="all, delete-orphan")
    logs = relationship("Log", back_populates="input", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Input(id={self.id}, name={self.name}, udp_port={self.udp_port})>"


class Output(Base):
    """Output stream model."""
    __tablename__ = "outputs"

    id = Column(Integer, primary_key=True, index=True)
    input_id = Column(Integer, ForeignKey("inputs.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    url = Column(String(1024), nullable=False)
    protocol = Column(Enum(ProtocolType), nullable=False)
    status = Column(Enum(OutputStatus), default=OutputStatus.STOPPED)
    auto_reconnect = Column(Boolean, default=True)
    reconnect_delay = Column(Integer, default=5)
    reconnect_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    process_id = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    input = relationship("Input", back_populates="outputs")
    logs = relationship("Log", back_populates="output", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Output(id={self.id}, name={self.name}, protocol={self.protocol})>"


class Log(Base):
    """Log entries model."""
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False)  # 'input' or 'output' or 'system'
    entity_id = Column(Integer, nullable=True)
    input_id = Column(Integer, ForeignKey("inputs.id", ondelete="CASCADE"), nullable=True)
    output_id = Column(Integer, ForeignKey("outputs.id", ondelete="CASCADE"), nullable=True)
    level = Column(Enum(LogLevel), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    input = relationship("Input", back_populates="logs")
    output = relationship("Output", back_populates="logs")

    def __repr__(self):
        return f"<Log(id={self.id}, level={self.level}, entity_type={self.entity_type})>"


class Setting(Base):
    """Application settings model."""
    __tablename__ = "settings"

    key = Column(String(255), primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Setting(key={self.key}, value={self.value})>"
