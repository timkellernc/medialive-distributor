# Stream Distribution Manager - Documentation Index

## 📚 Quick Navigation

### 🚀 Getting Started (Start Here!)

1. **[README.md](README.md)** - Main project overview and introduction
2. **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
3. **[INSTALLATION.md](INSTALLATION.md)** - Detailed installation instructions

### 📖 Core Documentation

4. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Comprehensive project overview
5. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and architecture
6. **[API.md](API.md)** - Complete API reference
7. **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide

### 🔧 Configuration & Setup

- **[.env.example](.env.example)** - Environment configuration template
- **[docker-compose.yml](docker-compose.yml)** - Docker services configuration
- **[requirements.txt](requirements.txt)** - Python dependencies

### 📝 Legal & Licensing

- **[LICENSE](LICENSE)** - MIT License

---

## 📖 Documentation Guide by Role

### For Developers

**Getting Started:**
1. [INSTALLATION.md](INSTALLATION.md) - Method 3: Development Setup
2. [ARCHITECTURE.md](ARCHITECTURE.md) - Understand the system
3. [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Technology stack

**Development:**
- `app/` directory - Application code
- `tests/` directory - Test suite
- [API.md](API.md) - API endpoints
- [README.md](README.md) - Contributing section

**Testing:**
- `pytest.ini` - Test configuration
- `tests/test_api.py` - Example tests
- Run: `pytest --cov=app`

### For System Administrators

**Installation:**
1. [INSTALLATION.md](INSTALLATION.md) - Complete installation guide
2. [QUICKSTART.md](QUICKSTART.md) - Quick Docker setup
3. [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment

**Operations:**
- [DEPLOYMENT.md](DEPLOYMENT.md) - Backup, monitoring, scaling
- [docker-compose.yml](docker-compose.yml) - Service configuration
- [.env.example](.env.example) - Environment variables

**Troubleshooting:**
- [INSTALLATION.md](INSTALLATION.md) - Troubleshooting section
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production issues
- [README.md](README.md) - Common problems

### For End Users

**Getting Started:**
1. [QUICKSTART.md](QUICKSTART.md) - Start here!
2. [README.md](README.md) - Basic usage
3. Web UI at `http://localhost:8080`

**Usage:**
- [QUICKSTART.md](QUICKSTART.md) - Common use cases
- [README.md](README.md) - Basic operations
- Web UI - Interactive interface

### For DevOps/SRE

**Deployment:**
1. [DEPLOYMENT.md](DEPLOYMENT.md) - Production best practices
2. [INSTALLATION.md](INSTALLATION.md) - Platform-specific guides
3. [docker-compose.yml](docker-compose.yml) - Service orchestration

**Monitoring:**
- [DEPLOYMENT.md](DEPLOYMENT.md) - Monitoring setup
- [API.md](API.md) - Health check endpoints
- [ARCHITECTURE.md](ARCHITECTURE.md) - System metrics

**Scaling:**
- [DEPLOYMENT.md](DEPLOYMENT.md) - Scaling strategies
- [ARCHITECTURE.md](ARCHITECTURE.md) - Scalability section
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Capabilities

---

## 📂 File Structure Overview

### Documentation Files
```
├── INDEX.md                    ← You are here
├── README.md                   ← Start here for overview
├── QUICKSTART.md              ← 5-minute getting started
├── INSTALLATION.md            ← Detailed installation
├── PROJECT_SUMMARY.md         ← Comprehensive summary
├── ARCHITECTURE.md            ← System architecture
├── API.md                     ← API reference
├── DEPLOYMENT.md              ← Production deployment
└── LICENSE                    ← MIT License
```

### Application Files
```
app/
├── main.py                    ← Application entry point
├── config.py                  ← Configuration
├── database.py                ← Database setup
├── models.py                  ← Data models
├── schemas.py                 ← API schemas
├── api/                       ← API routes
│   ├── inputs.py
│   ├── outputs.py
│   └── system.py
├── services/                  ← Business logic
│   ├── input_service.py
│   ├── output_service.py
│   ├── mediamtx_service.py
│   └── ffmpeg_service.py
└── static/                    ← Web UI
    └── index.html
```

### Configuration Files
```
├── docker-compose.yml         ← Docker services
├── Dockerfile                 ← App container
├── requirements.txt           ← Python dependencies
├── .env.example              ← Environment template
├── .gitignore                ← Git ignore rules
├── pytest.ini                ← Test configuration
└── start.sh                  ← Startup script
```

---

## 🎯 Common Tasks Quick Reference

### First Time Setup
1. Read [QUICKSTART.md](QUICKSTART.md)
2. Run `./start.sh`
3. Access http://localhost:8080

### Adding a Feature
1. Read [ARCHITECTURE.md](ARCHITECTURE.md)
2. Review `app/services/` for business logic
3. Add tests in `tests/`
4. Update [API.md](API.md) if adding endpoints

### Production Deployment
1. Read [DEPLOYMENT.md](DEPLOYMENT.md)
2. Configure [.env.example](.env.example)
3. Set up Nginx reverse proxy
4. Configure monitoring

### Troubleshooting
1. Check [INSTALLATION.md](INSTALLATION.md) - Troubleshooting
2. Review `docker-compose logs -f`
3. Test with API health check
4. Check [README.md](README.md) - Common issues

### API Integration
1. Read [API.md](API.md)
2. Get API key from `.env`
3. Test with curl examples
4. Review [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - API section

---

## 📊 Documentation Statistics

- **Total Documents**: 9 markdown files
- **Total Lines**: ~2,500 lines
- **Code Files**: 15 Python files
- **Test Files**: 1 test suite
- **Configuration Files**: 5 files

---

## 🔍 Search Guide

### Looking for specific topics?

**Installation topics:**
- Docker setup → [INSTALLATION.md](INSTALLATION.md)
- Development setup → [INSTALLATION.md](INSTALLATION.md)
- First run → [QUICKSTART.md](QUICKSTART.md)

**Configuration topics:**
- Environment variables → [.env.example](.env.example)
- Docker services → [docker-compose.yml](docker-compose.yml)
- Security → [DEPLOYMENT.md](DEPLOYMENT.md)

**API topics:**
- Endpoints → [API.md](API.md)
- Authentication → [API.md](API.md)
- WebSocket → [API.md](API.md)

**Architecture topics:**
- System design → [ARCHITECTURE.md](ARCHITECTURE.md)
- Data flow → [ARCHITECTURE.md](ARCHITECTURE.md)
- Scaling → [ARCHITECTURE.md](ARCHITECTURE.md)

**Operations topics:**
- Production → [DEPLOYMENT.md](DEPLOYMENT.md)
- Monitoring → [DEPLOYMENT.md](DEPLOYMENT.md)
- Backup → [DEPLOYMENT.md](DEPLOYMENT.md)

---

## 📱 Quick Links

- **Web UI**: http://localhost:8080
- **API Health**: http://localhost:8080/api/health
- **API Base**: http://localhost:8080/api
- **MediaMTX API**: http://localhost:9997
- **Default API Key**: `your-secret-api-key-change-in-production`

---

## 🆘 Getting Help

1. **Installation issues** → [INSTALLATION.md](INSTALLATION.md)
2. **Usage questions** → [QUICKSTART.md](QUICKSTART.md)
3. **API questions** → [API.md](API.md)
4. **Production issues** → [DEPLOYMENT.md](DEPLOYMENT.md)
5. **Architecture questions** → [ARCHITECTURE.md](ARCHITECTURE.md)

---

## ✅ Document Checklist

Before starting, make sure you've read:

- [ ] [README.md](README.md) - Project overview
- [ ] [QUICKSTART.md](QUICKSTART.md) - Get it running
- [ ] [INSTALLATION.md](INSTALLATION.md) - Installation method
- [ ] [API.md](API.md) - If using API
- [ ] [DEPLOYMENT.md](DEPLOYMENT.md) - If deploying to production

---

**Last Updated**: November 2024
**Version**: 1.0.0
**Maintained By**: Stream Distribution Manager Team
