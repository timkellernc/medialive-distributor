"""MediaMTX service for configuration and health management."""

import yaml
import httpx
import logging
from typing import Dict, Optional, List
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)


class MediaMTXService:
    """Service for managing MediaMTX configuration and health."""

    def __init__(self):
        self.config_path = Path(settings.mediamtx_config_path)
        self.api_url = settings.mediamtx_api_url
        self.api_timeout = settings.mediamtx_api_timeout

    async def check_health(self) -> bool:
        """Check if MediaMTX API is available."""
        try:
            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                response = await client.get(f"{self.api_url}/v3/config/get")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"MediaMTX health check failed: {e}")
            return False

    async def get_paths(self) -> List[str]:
        """Get list of configured paths from MediaMTX."""
        try:
            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                response = await client.get(f"{self.api_url}/v3/paths/list")
                if response.status_code == 200:
                    data = response.json()
                    return [item.get("name", "") for item in data.get("items", [])]
        except Exception as e:
            logger.error(f"Failed to get MediaMTX paths: {e}")
        return []

    def load_config(self) -> Dict:
        """Load current MediaMTX configuration."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f) or {}
            else:
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Failed to load MediaMTX config: {e}")
            return self._get_default_config()

    def save_config(self, config: Dict) -> bool:
        """Save MediaMTX configuration to file."""
        try:
            # Ensure config directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"MediaMTX config saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save MediaMTX config: {e}")
            return False

    def add_input_path(self, path_name: str, udp_port: int, srt_port: int) -> bool:
        """Add a new input path to MediaMTX configuration."""
        try:
            config = self.load_config()
            
            if 'paths' not in config:
                config['paths'] = {}
            
            config['paths'][path_name] = {
                'source': f'udp://0.0.0.0:{udp_port}',
                'sourceProtocol': 'udp',
                'runOnReady': '',
                'runOnNotReady': ''
            }
            
            return self.save_config(config)
        except Exception as e:
            logger.error(f"Failed to add input path {path_name}: {e}")
            return False

    def remove_input_path(self, path_name: str) -> bool:
        """Remove an input path from MediaMTX configuration."""
        try:
            config = self.load_config()
            
            if 'paths' in config and path_name in config['paths']:
                del config['paths'][path_name]
                return self.save_config(config)
            
            return True  # Already removed
        except Exception as e:
            logger.error(f"Failed to remove input path {path_name}: {e}")
            return False

    async def reload_config(self) -> bool:
        """Trigger MediaMTX to reload configuration."""
        try:
            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                response = await client.post(f"{self.api_url}/v3/config/pathsadd/all")
                return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Failed to reload MediaMTX config: {e}")
            return False

    def _get_default_config(self) -> Dict:
        """Get default MediaMTX configuration."""
        return {
            'logLevel': 'info',
            'logDestinations': ['stdout'],
            'logFile': '',
            
            'api': True,
            'apiAddress': ':9997',
            
            'metrics': True,
            'metricsAddress': ':9998',
            
            'pprof': False,
            'pprofAddress': ':9999',
            
            'runOnConnect': '',
            'runOnConnectRestart': False,
            'runOnDisconnect': '',
            
            'rtsp': True,
            'rtspAddress': ':8554',
            'protocols': ['tcp', 'udp'],
            'encryption': 'no',
            'rtspAddress': ':8554',
            
            'rtmp': False,
            'rtmpAddress': ':1935',
            
            'hls': False,
            'hlsAddress': ':8888',
            
            'webrtc': False,
            'webrtcAddress': ':8889',
            
            'srt': True,
            'srtAddress': ':8890',
            
            'paths': {}
        }

    def get_srt_url(self, path_name: str, srt_port: int) -> str:
        """Get SRT URL for a given input path."""
        # MediaMTX SRT URL format
        return f"srt://mediamtx:{srt_port}?streamid=read:{path_name}"

    def validate_config(self, config: Dict) -> tuple[bool, Optional[str]]:
        """Validate MediaMTX configuration."""
        required_fields = ['api', 'apiAddress', 'paths']
        
        for field in required_fields:
            if field not in config:
                return False, f"Missing required field: {field}"
        
        if not isinstance(config.get('paths'), dict):
            return False, "Paths must be a dictionary"
        
        return True, None


# Singleton instance
mediamtx_service = MediaMTXService()
