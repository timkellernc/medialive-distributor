"""Configuration management for Stream Distribution Manager."""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Stream Distribution Manager"
    app_version: str = "1.0.0"
    port: int = 8080
    host: str = "0.0.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # Security
    secret_key: str = "change-this-secret-key-in-production"
    api_key: str = "your-secret-api-key-change-in-production"
    cors_origins: list = ["*"]

    # Database
    database_url: str = "sqlite:///./stream_manager.db"

    # MediaMTX
    mediamtx_config_path: str = "/config/mediamtx.yml"
    mediamtx_api_url: str = "http://mediamtx:9997"
    mediamtx_api_timeout: int = 10

    # Port Ranges
    udp_port_range_start: int = 5000
    udp_port_range_end: int = 5100
    srt_port_range_start: int = 8890
    srt_port_range_end: int = 8990

    # FFmpeg Defaults
    default_reconnect_delay: int = 5
    max_reconnect_attempts: int = 0  # 0 = infinite
    ffmpeg_log_level: str = "error"
    ffmpeg_timeout: int = 30

    # Process Management
    max_outputs_per_input: int = 20
    process_check_interval: int = 5
    process_restart_delay: int = 3

    # Logging
    log_retention_days: int = 7
    log_max_entries: int = 1000

    # WebSocket
    websocket_ping_interval: int = 25
    websocket_ping_timeout: int = 20

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export settings instance
settings = get_settings()
