# System Architecture

## Overview

Stream Distribution Manager is a microservices-based application for managing live video stream distribution. It receives UDP input streams, processes them through MediaMTX, and distributes them to multiple output destinations using FFmpeg.

## Architecture Diagram

```
┌──────────────┐
│   UDP Input  │ (Port 5000-5100)
│   Streams    │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────┐
│         MediaMTX                 │
│  - Receives UDP streams          │
│  - Converts to SRT               │
│  - Manages stream paths          │
│  - API on port 9997              │
└──────┬───────────────────────────┘
       │ SRT (Port 8890+)
       ▼
┌──────────────────────────────────┐
│    FFmpeg Processes              │
│  - One process per output        │
│  - Reads from MediaMTX SRT       │
│  - Writes to destinations        │
│  - Auto-reconnect on failure     │
└──────┬───────────────────────────┘
       │
       ├─────► SRT Outputs
       ├─────► RTMP Outputs (YouTube, Facebook, etc.)
       ├─────► UDP Outputs
       └─────► RTSP Outputs

┌──────────────────────────────────┐
│      FastAPI Backend             │
│  - REST API                      │
│  - WebSocket for real-time       │
│  - Process management            │
│  - Database operations           │
└──────┬───────────────────────────┘
       │
       ├─────► SQLite/PostgreSQL
       │        (Data persistence)
       │
       └─────► Web UI
                (Vue.js/Bootstrap)
```

## Component Details

### 1. Web UI (Frontend)

**Technology**: HTML5, Bootstrap 5, JavaScript
**Purpose**: User interface for managing streams
**Features**:
- Dashboard with system statistics
- Input management (create, view, delete)
- Output management (add, start, stop, monitor)
- Real-time status updates via WebSocket
- Responsive design

### 2. FastAPI Backend

**Technology**: Python 3.11+, FastAPI, SQLAlchemy
**Purpose**: Application server and business logic
**Responsibilities**:
- REST API endpoints
- WebSocket server for real-time updates
- Authentication and authorization
- Database operations
- Process orchestration

**Key Modules**:
- `app/main.py`: Application entry point
- `app/config.py`: Configuration management
- `app/database.py`: Database connection
- `app/models.py`: SQLAlchemy models
- `app/schemas.py`: Pydantic schemas
- `app/api/`: API route handlers
- `app/services/`: Business logic layer

### 3. Services Layer

#### Input Service
**File**: `app/services/input_service.py`
**Purpose**: Manage input streams
**Functions**:
- Create/update/delete inputs
- Port allocation
- MediaMTX path generation
- Input statistics

#### Output Service
**File**: `app/services/output_service.py`
**Purpose**: Manage output streams
**Functions**:
- Create/update/delete outputs
- Start/stop outputs
- Output statistics and logs
- FFmpeg process coordination

#### MediaMTX Service
**File**: `app/services/mediamtx_service.py`
**Purpose**: Integrate with MediaMTX
**Functions**:
- Configuration management
- Health monitoring
- Dynamic path management
- API communication

#### FFmpeg Service
**File**: `app/services/ffmpeg_service.py`
**Purpose**: Manage FFmpeg processes
**Functions**:
- Process lifecycle management
- Command generation
- Auto-reconnect logic
- Resource monitoring

### 4. MediaMTX

**Technology**: Go-based media server
**Purpose**: Stream routing and protocol conversion
**Responsibilities**:
- Receive UDP streams
- Convert to SRT for FFmpeg
- Manage stream paths
- Provide health API

**Configuration**: Dynamic YAML configuration managed by the application

### 5. FFmpeg Processes

**Technology**: FFmpeg (system package)
**Purpose**: Stream transcoding and distribution
**Pattern**: One process per output
**Features**:
- Copy mode (no re-encoding)
- Auto-reconnect on failure
- Resource monitoring
- Graceful shutdown

### 6. Database

**Technology**: SQLite (dev) / PostgreSQL (prod)
**Purpose**: Persistent data storage
**Tables**:
- `inputs`: Input stream configuration
- `outputs`: Output stream configuration
- `logs`: Application logs
- `settings`: System settings

## Data Flow

### Creating an Input Stream

1. User submits input creation via Web UI
2. FastAPI validates request
3. InputService allocates UDP and SRT ports
4. InputService generates MediaMTX path
5. InputService creates database record
6. MediaMTXService updates configuration
7. MediaMTX loads new path
8. Success response returned to user

### Adding an Output

1. User submits output creation via Web UI
2. FastAPI validates request and protocol
3. OutputService creates database record
4. OutputService calls FFmpegService
5. FFmpegService builds FFmpeg command
6. FFmpegService starts process
7. Process monitored for health
8. Status updates sent via WebSocket

### Auto-Reconnect Flow

1. FFmpeg process exits (network failure)
2. Monitor detects process death
3. Wait reconnect_delay seconds
4. Restart FFmpeg process
5. Update reconnect_count
6. Send status update via WebSocket
7. Repeat if process fails again

## Network Architecture

### Ports

**Application**: 8080 (HTTP/WebSocket)
**MediaMTX API**: 9997
**UDP Inputs**: 5000-5100 (configurable)
**SRT Outputs**: 8890-8990 (configurable)
**Database**: 5432 (PostgreSQL, internal only)

### Docker Network

All containers communicate via internal Docker network:
- App ↔ Database: Direct connection
- App ↔ MediaMTX: HTTP API + SRT
- App ↔ FFmpeg: Process management (same container)

## Security Architecture

### Authentication
- API key-based authentication
- Required header: `X-API-Key`
- Configurable via environment variable

### Input Validation
- Pydantic schemas for request validation
- SQLAlchemy for database validation
- URL format validation per protocol

### Process Isolation
- FFmpeg runs as non-root user
- Containers use minimal base images
- No shell access in production

### Network Security
- Internal Docker network for services
- Exposed only necessary ports
- CORS configuration

## Scalability Considerations

### Current Limits
- Max inputs: Limited by port range (default 101)
- Max outputs per input: 20 (configurable)
- Max concurrent outputs: ~200 (depends on hardware)

### Scaling Options

**Vertical Scaling**:
- Increase container CPU/memory limits
- Add hardware acceleration (GPU)
- Optimize FFmpeg parameters

**Horizontal Scaling**:
- Run multiple app instances
- Use external PostgreSQL
- Shared MediaMTX cluster
- Load balancer for web UI

### Performance Optimization

**FFmpeg**:
- Use copy mode (no transcoding)
- Hardware acceleration where available
- Tune buffer sizes

**Database**:
- Connection pooling
- Proper indexing
- Regular vacuum (PostgreSQL)

**API**:
- Async endpoints
- WebSocket for real-time updates
- Caching where appropriate

## Monitoring and Observability

### Metrics Collected
- System: CPU, memory, disk
- Streams: Input count, output count, active outputs
- Processes: FFmpeg PIDs, resource usage
- Health: MediaMTX status, database connectivity

### Logging
- Application logs: Structured JSON
- FFmpeg logs: Captured stderr
- Log levels: DEBUG, INFO, WARNING, ERROR
- Log rotation: Automatic cleanup

### Health Checks
- Application: `/api/health`
- MediaMTX: API connectivity
- Database: Connection test
- Docker: Container health checks

## Deployment Architecture

### Development
- SQLite database
- Single Docker Compose stack
- Hot reload enabled
- Debug logging

### Production
- PostgreSQL database
- Behind Nginx reverse proxy
- SSL/TLS termination
- Production logging
- Resource limits
- Auto-restart policies

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | HTML5, Bootstrap 5, JavaScript | Web UI |
| Backend API | FastAPI, Python 3.11+ | REST API |
| WebSocket | Socket.IO | Real-time updates |
| Database | SQLite / PostgreSQL | Data persistence |
| ORM | SQLAlchemy | Database abstraction |
| Validation | Pydantic | Request/response validation |
| Media Router | MediaMTX | Stream routing |
| Transcoder | FFmpeg | Stream distribution |
| Container | Docker | Containerization |
| Orchestration | Docker Compose | Multi-container management |
| Web Server | Nginx (optional) | Reverse proxy |

## Future Enhancements

- Stream recording capability
- Stream preview/thumbnails
- Bandwidth monitoring
- Email/webhook alerts
- User management system
- Multi-tenancy support
- Stream analytics dashboard
- Mobile app
