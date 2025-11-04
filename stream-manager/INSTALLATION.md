# Installation Guide

## System Requirements

### Minimum Requirements
- **OS**: Linux (Ubuntu 20.04+), macOS (10.15+), Windows 10+ with WSL2
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Disk**: 10 GB free space
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8+ GB
- **Disk**: 50+ GB SSD
- **Network**: 1 Gbps+

## Installation Methods

### Method 1: Quick Start (Recommended)

**Step 1: Clone the project**
```bash
git clone <repository-url>
cd stream-manager
```

**Step 2: Run the start script**
```bash
chmod +x start.sh
./start.sh
```

**Step 3: Access the application**
```
Open browser: http://localhost:8080
Default API Key: your-secret-api-key-change-in-production
```

That's it! You're ready to go.

---

### Method 2: Manual Docker Setup

**Step 1: Prepare environment**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Step 2: Create directories**
```bash
mkdir -p logs
```

**Step 3: Start services**
```bash
# Pull images
docker-compose pull

# Build application
docker-compose build

# Start all services
docker-compose up -d
```

**Step 4: Verify installation**
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f

# Test API
curl -H "X-API-Key: your-api-key" http://localhost:8080/api/health
```

---

### Method 3: Development Setup (Local)

**Step 1: Install system dependencies**

Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y python3.11 python3-pip ffmpeg
```

macOS:
```bash
brew install python@3.11 ffmpeg
```

**Step 2: Create virtual environment**
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Step 3: Install Python dependencies**
```bash
pip install -r requirements.txt
```

**Step 4: Install MediaMTX**
```bash
# Download from https://github.com/bluenviron/mediamtx/releases
wget https://github.com/bluenviron/mediamtx/releases/latest/download/mediamtx_vX.X.X_linux_amd64.tar.gz
tar -xzf mediamtx_*.tar.gz
```

**Step 5: Configure environment**
```bash
cp .env.example .env
# Edit .env with local paths
```

**Step 6: Initialize database**
```bash
python -c "from app.database import init_db; init_db()"
```

**Step 7: Start MediaMTX**
```bash
./mediamtx mediamtx.yml
```

**Step 8: Start application** (in another terminal)
```bash
source venv/bin/activate
python -m app.main
```

---

## Post-Installation

### 1. Verify Installation

```bash
# Check all containers are running
docker-compose ps

# Expected output:
# NAME                      STATUS
# stream-manager-app        Up (healthy)
# stream-manager-mediamtx   Up (healthy)
```

### 2. Test Basic Functionality

**Create an input via API:**
```bash
curl -X POST http://localhost:8080/api/inputs \
  -H "X-API-Key: your-secret-api-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Input"}'
```

**Send a test stream:**
```bash
# Replace test.mp4 with your video file
# Replace 5001 with your assigned UDP port
ffmpeg -re -i test.mp4 -c copy -f mpegts udp://localhost:5001
```

**Add an output:**
```bash
curl -X POST http://localhost:8080/api/inputs/1/outputs \
  -H "X-API-Key: your-secret-api-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Output",
    "url": "udp://127.0.0.1:6000",
    "protocol": "udp"
  }'
```

### 3. Security Configuration

**Change default credentials:**
```bash
# Generate strong API key
openssl rand -hex 32

# Update .env file
API_KEY=<your-generated-key>
SECRET_KEY=<another-generated-key>

# Restart services
docker-compose restart
```

### 4. Configure Firewall

```bash
# Ubuntu/Debian
sudo ufw allow 8080/tcp     # Web UI
sudo ufw allow 5000:5100/udp  # UDP inputs
sudo ufw allow 8890:8990/udp  # SRT ports
```

---

## Platform-Specific Instructions

### Windows (WSL2)

1. **Install WSL2**
```powershell
wsl --install
```

2. **Install Docker Desktop for Windows**
   - Download from docker.com
   - Enable WSL2 backend
   - Start Docker Desktop

3. **Open WSL2 terminal and follow Linux instructions**

### macOS

1. **Install Docker Desktop for Mac**
   - Download from docker.com
   - Install and start Docker Desktop

2. **Open Terminal and follow standard instructions**

### Linux (Ubuntu/Debian)

1. **Install Docker**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

2. **Install Docker Compose**
```bash
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

3. **Log out and back in, then follow standard instructions**

---

## Troubleshooting Installation

### Port Already in Use

```bash
# Find process using port 8080
sudo lsof -i :8080
# or
sudo netstat -tulpn | grep 8080

# Kill the process or change port in docker-compose.yml
```

### Permission Denied

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in
```

### Container Won't Start

```bash
# Check logs
docker-compose logs app

# Common issues:
# 1. Port conflicts - change ports in docker-compose.yml
# 2. Insufficient memory - check docker stats
# 3. Config errors - verify .env file
```

### MediaMTX Connection Failed

```bash
# Check MediaMTX is running
docker logs stream-manager-mediamtx

# Restart MediaMTX
docker restart stream-manager-mediamtx

# Check network connectivity
docker exec stream-manager-app curl http://mediamtx:9997/v3/config/get
```

---

## Upgrading

### From Docker

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Backup Before Upgrade

```bash
# Backup database
docker exec stream-manager-app cp /data/stream_manager.db /data/backup.db

# Backup configuration
cp .env .env.backup
```

---

## Uninstallation

### Remove Everything

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Remove images
docker rmi stream-manager-app
docker rmi bluenviron/mediamtx

# Remove project directory
cd ..
rm -rf stream-manager
```

### Keep Data

```bash
# Stop containers but keep volumes
docker-compose down

# Remove only project files
cd ..
rm -rf stream-manager
```

---

## Next Steps

After installation:

1. **Read the Quick Start**: [QUICKSTART.md](QUICKSTART.md)
2. **Explore the API**: [API.md](API.md)
3. **Configure for Production**: [DEPLOYMENT.md](DEPLOYMENT.md)
4. **Understand the Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## Getting Help

- Check logs: `docker-compose logs -f`
- View status: `docker-compose ps`
- Test API: `curl http://localhost:8080/api/health`
- Read documentation files
- Check GitHub issues

---

**Installation complete! Ready to start streaming! 🎥**
