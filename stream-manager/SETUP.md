# Setup Instructions

## Quick Setup (Ubuntu Server)

### 1. Extract the archive
```bash
tar -xzf stream-manager.tar.gz
cd stream-manager
```

### 2. Create .env file
```bash
cp .env.example .env
```

### 3. Make start script executable
```bash
chmod +x start.sh
```

### 4. Start the application
```bash
# Option A: Using the script
./start.sh

# Option B: Manually
docker-compose up -d
```

### 5. Access the application
```
http://your-server-ip:8080
Default API Key: your-secret-api-key-change-in-production
```

## Verify Installation

```bash
# Check containers are running
docker-compose ps

# View logs
docker-compose logs -f

# Test API
curl -H "X-API-Key: your-secret-api-key-change-in-production" http://localhost:8080/api/health
```

## What's Included

```
stream-manager/
├── config/
│   └── mediamtx.yml          ✓ MediaMTX configuration
├── app/
│   ├── api/                  ✓ API routes (inputs, outputs, system)
│   ├── services/             ✓ Business logic
│   ├── static/               ✓ Web UI
│   └── *.py                  ✓ Core application files
├── logs/                     ✓ Log directory
├── tests/                    ✓ Test suite
├── docker-compose.yml        ✓ Container orchestration
├── Dockerfile               ✓ Application container
├── requirements.txt         ✓ Python dependencies
├── .env.example            ✓ Environment template
├── start.sh                ✓ Startup script
└── Documentation/          ✓ Complete docs (10 files)
```

## Troubleshooting

### MediaMTX not starting?
The `config/mediamtx.yml` file is now included. It should work automatically.

### Permission issues?
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### Port conflicts?
Edit `docker-compose.yml` and change the port mappings.

## Next Steps

1. Read `INDEX.md` for documentation navigation
2. Read `QUICKSTART.md` for 5-minute guide
3. Read `INSTALLATION.md` for detailed setup
4. Access web UI at http://localhost:8080

## Security (Production)

Generate secure keys:
```bash
openssl rand -hex 32
```

Update `.env` with the generated keys before production use.
