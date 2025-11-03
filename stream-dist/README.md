# Stream Distribution Manager

A production-ready Python web application for managing live video stream distribution. Receives UDP input streams, processes them through MediaMTX, and distributes them to multiple independent output destinations (SRT, RTMP, UDP).

## Features

- 🎥 **Multiple Input Streams**: Unlimited simultaneous UDP input streams
- 📡 **Multi-Protocol Output**: SRT (caller/listener), RTMP, UDP, RTSP support
- 🔄 **Auto-Reconnect**: Automatic reconnection on output failures
- 📊 **Real-time Monitoring**: WebSocket-based live status updates
- 🎨 **Modern Web UI**: Responsive interface with dark/light mode
- 🐳 **Docker Ready**: Complete Docker Compose setup
- 📈 **Health Monitoring**: MediaMTX and FFmpeg process monitoring
- 🔐 **Secure**: API key authentication and input validation

## Quick Start

### Prerequisites

- Docker and Docker Compose
- 4GB+ RAM recommended
- Linux/macOS/Windows with WSL2

### Installation

1. **Clone and navigate to the project:**
```bash
cd stream-manager
```

2. **Start the application:**
```bash
docker-compose up -d
```

3. **Access the web UI:**
```
http://localhost:8080
```

Default API key: `your-secret-api-key-change-in-production`

### Basic Usage

1. **Create an Input Stream:**
   - Navigate to "Inputs" page
   - Click "Add Input"
   - Enter name and UDP port (e.g., 5001)
   - Send your stream to `udp://localhost:5001`

2. **Add Output Destinations:**
   - Click on your input stream
   - Click "Add Output"
   - Choose protocol and enter destination
   - Output starts automatically

3. **Monitor Streams:**
   - View real-time status on dashboard
   - Check individual output logs
   - Monitor resource usage

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=sqlite:///./stream_manager.db
# For PostgreSQL: postgresql://user:pass@postgres:5432/streamdb

# Security
SECRET_KEY=your-secret-key-change-this
API_KEY=your-secret-api-key-change-in-production

# MediaMTX
MEDIAMTX_CONFIG_PATH=/config/mediamtx.yml
MEDIAMTX_API_URL=http://mediamtx:9997

# Application
LOG_LEVEL=INFO
PORT=8080

# Input/Output Defaults
DEFAULT_RECONNECT_DELAY=5
MAX_RECONNECT_ATTEMPTS=0  # 0 = infinite
UDP_PORT_RANGE_START=5000
UDP_PORT_RANGE_END=5100
SRT_PORT_RANGE_START=8890
```

### Development Setup

1. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install FFmpeg:**
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows: Download from ffmpeg.org
```

4. **Run MediaMTX locally:**
```bash
# Download MediaMTX from github.com/bluenviron/mediamtx
./mediamtx mediamtx.yml
```

5. **Run the application:**
```bash
python -m app.main
```

## Architecture

```
┌─────────────┐
│   Web UI    │ ← User Interface (Vue.js)
└──────┬──────┘
       │ HTTP/WebSocket
┌──────▼──────┐
│  FastAPI    │ ← Application Server
│  Backend    │
└──────┬──────┘
       │
       ├─────────► SQLite/PostgreSQL (Data persistence)
       │
       ├─────────► MediaMTX (Stream routing)
       │            - Receives UDP inputs
       │            - Provides SRT outputs
       │
       └─────────► FFmpeg Processes (Stream distribution)
                    - One process per output
                    - Auto-reconnect on failure
```

## API Documentation

See [API.md](./API.md) for complete API documentation.

### Quick API Examples

**Create an input:**
```bash
curl -X POST http://localhost:8080/api/inputs \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "Camera 1", "udp_port": 5001}'
```

**Add an output:**
```bash
curl -X POST http://localhost:8080/api/inputs/1/outputs \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "YouTube",
    "url": "rtmp://a.rtmp.youtube.com/live2/your-stream-key",
    "protocol": "rtmp"
  }'
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run integration tests
pytest tests/integration/
```

## Production Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed production deployment guide including:
- PostgreSQL setup
- Nginx reverse proxy
- SSL/TLS configuration
- Monitoring and alerting
- Backup strategies
- Performance tuning

## Troubleshooting

### Common Issues

**Issue: Output keeps reconnecting**
- Check destination is reachable: `telnet <ip> <port>`
- Verify URL format is correct
- Check FFmpeg logs in the UI

**Issue: Input shows no data**
- Verify stream is sending to correct UDP port
- Check MediaMTX logs: `docker logs stream-manager-mediamtx-1`
- Test with: `ffmpeg -re -i test.mp4 -f mpegts udp://localhost:5001`

**Issue: High CPU usage**
- Reduce number of simultaneous outputs
- Check FFmpeg process count: `docker exec stream-manager-app ps aux | grep ffmpeg`
- Consider hardware acceleration options

**Issue: Docker containers won't start**
- Check port availability: `netstat -tulpn | grep 8080`
- Review logs: `docker-compose logs`
- Verify enough disk space and memory

### Logs

View application logs:
```bash
docker-compose logs -f app
```

View MediaMTX logs:
```bash
docker-compose logs -f mediamtx
```

View all logs:
```bash
docker-compose logs -f
```

## Project Structure

```
stream-manager/
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database setup
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── api/                 # API routes
│   ├── services/            # Business logic
│   ├── utils/               # Utilities
│   └── static/              # Frontend files
├── tests/                   # Test suite
├── docker/                  # Docker configs
├── docs/                    # Documentation
├── requirements.txt         # Python dependencies
├── Dockerfile              # Application container
├── docker-compose.yml      # Multi-container setup
└── README.md               # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure tests pass: `pytest`
5. Format code: `black . && flake8`
6. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- 📚 Documentation: [docs/](./docs/)
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions

## Roadmap

- [ ] Stream recording capability
- [ ] Stream preview/thumbnails
- [ ] Bandwidth monitoring
- [ ] Email/webhook alerts
- [ ] User management system
- [ ] Stream analytics dashboard
- [ ] Mobile app

---

**Note:** This application is designed for professional streaming workflows. Always test in a development environment before production deployment.
