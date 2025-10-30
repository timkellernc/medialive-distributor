# MediaLive Distributor - Project Structure

```
medialive-distributor/
├── app.py                          # Main application (FastAPI + FFmpeg management)
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container image definition
├── docker-compose.yml              # Docker Compose deployment configuration
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
│
├── static/
│   └── index.html                  # Web dashboard (HTML/CSS/JavaScript)
│
├── systemd/
│   └── medialive-distributor.service  # Systemd service file
│
├── config/                         # Configuration storage (created at runtime)
│   └── channels.json               # Channel configurations (auto-generated)
│
├── logs/                           # Application logs (optional, created at runtime)
│
├── README.md                       # Complete documentation
├── QUICKSTART.md                   # 5-minute setup guide
├── DEPLOYMENT.md                   # Production deployment guide
├── EXAMPLES.md                     # Configuration examples
│
├── test.sh                         # Automated test suite
└── install-systemd.sh              # Systemd installation script
```

## File Descriptions

### Core Application Files

**app.py** (1,200 lines)
- FastAPI web server and RESTful API
- Channel and output management
- FFmpeg process lifecycle management
- WebSocket support for real-time updates
- Configuration persistence
- Health monitoring

**static/index.html** (600 lines)
- Responsive web dashboard
- Real-time status updates via WebSocket
- Channel creation and management UI
- Output configuration interface
- No build step required - pure HTML/CSS/JS

**requirements.txt**
- FastAPI - Web framework
- Uvicorn - ASGI server
- Pydantic - Data validation
- WebSockets - Real-time communication

### Deployment Files

**Dockerfile**
- Based on Python 3.11
- Includes FFmpeg
- Health check configured
- Production-ready

**docker-compose.yml**
- Service definition
- Port mappings (8000, 5000-5025/udp)
- Volume mounts for persistence
- Resource limits
- Logging configuration

**systemd/medialive-distributor.service**
- Alternative to Docker deployment
- Auto-restart configuration
- Security hardening
- Resource limits

**install-systemd.sh**
- Automated systemd installation
- Creates user and directories
- Installs dependencies
- Sets up service

### Documentation

**README.md** - Comprehensive documentation
- Features overview
- Architecture explanation
- Setup instructions
- API reference
- Usage guide
- Troubleshooting

**QUICKSTART.md** - Fast setup guide
- 5-minute deployment
- First channel setup
- Common URL examples
- Quick troubleshooting

**DEPLOYMENT.md** - Production guide
- Pre-deployment checklist
- Network configuration
- Performance optimization
- High availability setup
- Security hardening
- Monitoring procedures
- Backup and recovery

**EXAMPLES.md** - Configuration examples
- Single channel, multiple outputs
- Multi-channel setup
- SCTE-35 workflow
- High availability
- Testing setup
- Live event workflow
- Bulk operations scripts

### Testing & Utilities

**test.sh**
- Automated test suite
- API endpoint tests
- Channel lifecycle tests
- Output management tests
- Web interface validation

**.env.example**
- Environment variable template
- Configuration options
- Documentation

**.gitignore**
- Python artifacts
- Configuration files
- Logs
- IDE files

## Runtime Directories

These directories are created automatically:

**config/**
- Stores `channels.json`
- Persistent configuration
- Survives container restarts
- Should be backed up

**logs/** (optional)
- Application logs
- Rotated automatically
- For debugging

**/tmp/** (inside container)
- Named pipes (FIFOs) for stream distribution
- Temporary, cleared on restart

## Data Flow

```
MediaLive
    ↓ RTP/UDP
[Distributor Container]
    app.py (API/Management)
        ↓
    FFmpeg (Receiver) → FIFO
        ↓
    FFmpeg (Output 1) → SRT/RTMP
    FFmpeg (Output 2) → SRT/RTMP
    FFmpeg (Output N) → SRT/RTMP
```

## Port Usage

- **8000/tcp**: Web UI and REST API
- **5000-5025/udp**: RTP inputs from MediaLive
- **User-defined**: SRT/RTMP outputs (various)

## Configuration Storage

Configuration is stored in JSON format at `config/channels.json`:

```json
{
  "channel-uuid": {
    "config": {
      "name": "Channel Name",
      "rtp_ip": "192.168.1.100",
      "rtp_port": 5000,
      "outputs": [...]
    },
    "created_at": "2025-10-30T12:00:00"
  }
}
```

## Key Features Implementation

### Hot-Reload Outputs
- Each output runs as independent FFmpeg process
- Uses named pipes (FIFO) for stream distribution
- Adding/removing outputs doesn't affect others

### SCTE-35 Preservation
- `-c copy` flag preserves all MPEG-TS data
- `-copyts` maintains timestamps
- SRT protocol carries complete MPEG-TS

### Process Management
- Python subprocess for FFmpeg control
- Process groups for clean shutdown
- Automatic error detection
- Graceful restarts

### Web Dashboard
- WebSocket for real-time updates
- No page refresh needed
- Mobile-responsive design
- Works in any modern browser

## Scaling Architecture

**Single Server (Vertical):**
- 1-25 channels on one instance
- Docker resource limits
- Multiple CPU cores

**Multi-Server (Horizontal):**
- Multiple distributor instances
- Load balancer for web UI
- Different channels on different servers

## Security Model

- Private network deployment (no authentication by default)
- Add reverse proxy for public access
- Firewall restricts RTP ports to MediaLive IPs
- Docker security policies
- Read-only system paths

## Monitoring Points

1. **Health Check**: `/api/health`
2. **Channel Status**: Real-time in dashboard
3. **Output Status**: Per-output health, uptime, errors
4. **System Logs**: Docker logs or systemd journal
5. **FFmpeg Processes**: Process count and status

## Development vs Production

### Development
- Use `docker-compose.yml` as-is
- Single instance
- JSON file configuration
- Standard logging

### Production
- Consider host networking
- Multiple instances for HA
- Automated backups
- Enhanced monitoring
- Reverse proxy with auth
- Firewall rules
- Resource limits tuned

## Backup Strategy

**Critical Data:**
- `config/channels.json` - Must be backed up

**Recreatable:**
- Everything else can be rebuilt from source

**Backup Command:**
```bash
tar -czf backup-$(date +%Y%m%d).tar.gz config/
```

## Dependencies

**System:**
- Docker 20.10+
- Docker Compose 2.0+

**Container:**
- Python 3.11
- FFmpeg (latest)
- Linux kernel 5.x+

**External:**
- AWS MediaLive (source)
- SRT/RTMP destinations

## API Endpoints Summary

- `GET /api/health` - Health check
- `GET /api/channels` - List all channels
- `POST /api/channels` - Create channel
- `GET /api/channels/{id}` - Get channel details
- `DELETE /api/channels/{id}` - Delete channel
- `POST /api/channels/{id}/start` - Start channel
- `POST /api/channels/{id}/stop` - Stop channel
- `POST /api/channels/{id}/outputs` - Add output
- `DELETE /api/channels/{id}/outputs/{output_id}` - Remove output
- `PUT /api/channels/{id}/outputs/{output_id}` - Update output
- `WS /ws` - WebSocket for real-time updates

## Maintenance Tasks

**Regular:**
- Monitor disk space
- Check logs for errors
- Verify all outputs connected

**Periodic:**
- Backup configuration
- Update Docker images
- Review resource usage
- Check for updates

**As Needed:**
- Add/remove channels
- Adjust resource limits
- Scale horizontally
- Update configurations

---

**Total Lines of Code:** ~2,500  
**Languages:** Python, HTML/CSS/JavaScript, Bash  
**Container Size:** ~500MB  
**Memory Usage:** ~100MB base + ~20MB per channel  
**CPU Usage:** <1% per channel (remux only, no transcoding)
