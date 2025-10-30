# Production Deployment Guide

## Pre-Deployment Checklist

### System Requirements Verification

```bash
# Verify Docker version (20.10+)
docker --version

# Verify Docker Compose version (2.0+)
docker-compose --version

# Check available disk space (10GB+ recommended)
df -h

# Check network connectivity
ping -c 4 8.8.8.8

# Verify FFmpeg is available in container
docker run --rm python:3.11-slim sh -c "apt-get update && apt-get install -y ffmpeg && ffmpeg -version"
```

### Network Configuration

1. **Firewall Rules**

```bash
# Allow web interface (TCP)
sudo ufw allow 8000/tcp

# Allow RTP input ports (UDP)
sudo ufw allow 5000:5025/udp

# Optional: Restrict to specific IP ranges
sudo ufw allow from 10.0.0.0/8 to any port 5000:5025 proto udp
```

2. **Kernel Network Tuning**

```bash
# Increase UDP receive buffer
sudo sysctl -w net.core.rmem_max=134217728
sudo sysctl -w net.core.rmem_default=134217728

# Make permanent
echo "net.core.rmem_max=134217728" | sudo tee -a /etc/sysctl.conf
echo "net.core.rmem_default=134217728" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

## Deployment Options

### Option 1: Docker Compose (Recommended)

```bash
# 1. Clone/copy files to server
cd /opt
sudo mkdir medialive-distributor
sudo chown $USER:$USER medialive-distributor
cd medialive-distributor

# 2. Copy all application files
# - app.py
# - requirements.txt
# - Dockerfile
# - docker-compose.yml
# - static/index.html

# 3. Create directories
mkdir -p config logs

# 4. Build and start
docker-compose up -d

# 5. Verify
docker-compose ps
docker-compose logs -f
curl http://localhost:8000/api/health
```

### Option 2: Systemd Service

```bash
# 1. Run installation script
sudo chmod +x install-systemd.sh
sudo ./install-systemd.sh

# 2. Start service
sudo systemctl start medialive-distributor

# 3. Verify
sudo systemctl status medialive-distributor
curl http://localhost:8000/api/health
```

## Initial Configuration

### 1. Configure First Channel

```bash
# Via API
curl -X POST http://localhost:8000/api/channels \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Channel 1",
    "rtp_ip": "192.168.1.100",
    "rtp_port": 5000
  }'

# Or use Web UI at http://your-server:8000
```

### 2. Configure MediaLive Output

In AWS MediaLive:

1. Create UDP Output Group
2. Set Network destination:
   - Primary: `udp://your-server-ip:5000`
   - Backup: `udp://your-server-ip:5001` (optional)
3. Enable SCTE-35 passthrough
4. Save and start channel

### 3. Add Outputs

```bash
# Add SRT output
curl -X POST http://localhost:8000/api/channels/CHANNEL_ID/outputs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CDN SRT Feed",
    "protocol": "srt",
    "url": "srt://cdn.example.com:9000?streamid=publish/stream1"
  }'
```

## Monitoring & Health Checks

### Application Health

```bash
# Quick health check
curl http://localhost:8000/api/health

# Full status check
curl http://localhost:8000/api/channels | jq '.'
```

### Docker Monitoring

```bash
# Container status
docker-compose ps

# Resource usage
docker stats medialive-distributor

# Logs
docker-compose logs -f --tail=100
```

### System Monitoring

```bash
# CPU and memory
htop

# Network usage
iftop -i eth0

# UDP packet drops
netstat -su | grep -i "packet receive errors"
```

## Performance Optimization

### 1. Host Networking Mode

For better performance with many channels:

```yaml
# docker-compose.yml
services:
  medialive-distributor:
    network_mode: "host"
    # Remove ports section when using host mode
```

### 2. CPU Affinity

Pin container to specific CPU cores:

```yaml
# docker-compose.yml
services:
  medialive-distributor:
    cpuset: "0-7"  # Use cores 0-7
```

### 3. Memory Configuration

```yaml
# docker-compose.yml
services:
  medialive-distributor:
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 2G
    mem_swappiness: 0
```

## Backup & Disaster Recovery

### Configuration Backup

```bash
# Automated backup script
cat > /opt/backup-medialive.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/medialive"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
cd /opt/medialive-distributor
tar -czf $BACKUP_DIR/config-$DATE.tar.gz config/

# Keep only last 30 days
find $BACKUP_DIR -name "config-*.tar.gz" -mtime +30 -delete
EOF

chmod +x /opt/backup-medialive.sh

# Add to crontab (daily at 2 AM)
echo "0 2 * * * /opt/backup-medialive.sh" | crontab -
```

### Restore from Backup

```bash
# Stop application
docker-compose down

# Restore configuration
cd /opt/medialive-distributor
tar -xzf /opt/backups/medialive/config-YYYYMMDD_HHMMSS.tar.gz

# Start application
docker-compose up -d
```

## High Availability Setup

### Load Balancer Configuration (nginx)

```nginx
# /etc/nginx/sites-available/medialive-lb
upstream medialive_backend {
    least_conn;
    server 10.0.1.10:8000 max_fails=3 fail_timeout=30s;
    server 10.0.1.11:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name medialive.example.com;

    location / {
        proxy_pass http://medialive_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Keepalived for VIP (Optional)

```bash
# Install keepalived
sudo apt-get install keepalived

# /etc/keepalived/keepalived.conf
vrrp_instance VI_1 {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 100
    advert_int 1
    
    virtual_ipaddress {
        10.0.1.100/24
    }
}
```

## Security Hardening

### 1. Reverse Proxy with Authentication

```nginx
# /etc/nginx/sites-available/medialive
server {
    listen 443 ssl http2;
    server_name medialive.example.com;

    ssl_certificate /etc/ssl/certs/medialive.crt;
    ssl_certificate_key /etc/ssl/private/medialive.key;

    auth_basic "MediaLive Distributor";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 2. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 443/tcp # HTTPS
sudo ufw allow from 10.0.0.0/8 to any port 5000:5025 proto udp
sudo ufw enable
```

### 3. SELinux/AppArmor

```bash
# Docker with AppArmor
docker-compose.yml:
  security_opt:
    - apparmor:docker-default
```

## Troubleshooting

### Common Issues

**Problem: High packet loss**
```bash
# Check UDP buffer
netstat -su | grep "packet receive errors"

# Increase buffer
sudo sysctl -w net.core.rmem_max=268435456
```

**Problem: Container won't start**
```bash
# Check logs
docker-compose logs

# Check port conflicts
sudo netstat -tulpn | grep 8000

# Check disk space
df -h
```

**Problem: Outputs not connecting**
```bash
# Check FFmpeg logs
docker-compose exec medialive-distributor sh
ps aux | grep ffmpeg
kill -USR1 <ffmpeg-pid>  # Trigger log output

# Test connectivity
telnet destination-ip destination-port
```

**Problem: SCTE-35 not preserved**
```bash
# Verify MediaLive settings
# - SCTE-35 passthrough enabled
# - Container format: MPEG-TS

# Check output protocol
# - Only SRT preserves SCTE-35
# - RTMP does not support SCTE-35
```

## Maintenance Procedures

### Rolling Update (Zero Downtime)

```bash
# 1. Pull new code/images
git pull
docker-compose pull

# 2. Create new container
docker-compose up -d --no-deps --build medialive-distributor

# 3. Verify
docker-compose ps
curl http://localhost:8000/api/health

# 4. Old container will stop after new one is healthy
```

### Database Migration

```bash
# Configuration is in JSON format
# No database migration needed

# If changing config format:
cd /opt/medialive-distributor
python3 migrate-config.py  # Custom migration script if needed
```

### Log Rotation

```bash
# Docker log rotation (already configured in docker-compose.yml)
# Manual log rotation for systemd:

cat > /etc/logrotate.d/medialive << 'EOF'
/opt/medialive-distributor/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 medialive medialive
    sharedscripts
    postrotate
        systemctl reload medialive-distributor
    endscript
}
EOF
```

## Scaling Guidelines

### Vertical Scaling (Single Server)

| Channels | CPU Cores | RAM  | Network    |
|----------|-----------|------|------------|
| 1-5      | 4 cores   | 2GB  | 1GbE       |
| 6-15     | 8 cores   | 4GB  | 1GbE       |
| 16-25    | 16 cores  | 8GB  | 10GbE      |
| 26+      | Scale horizontally |

### Horizontal Scaling

For >25 channels, deploy multiple instances:

```bash
# Server 1: Channels 1-25
# Server 2: Channels 26-50

# Use DNS round-robin or load balancer for web UI
# Route different MediaLive outputs to different servers
```

## Support Contacts

- Documentation: README.md
- API Reference: README.md#api-reference
- GitHub Issues: [your-repo-url]

## Appendix

### Useful Commands

```bash
# Quick restart
docker-compose restart

# View real-time logs
docker-compose logs -f --tail=50

# Check FFmpeg processes
docker-compose exec medialive-distributor ps aux | grep ffmpeg

# Check disk usage
du -sh /opt/medialive-distributor/*

# Network diagnostics
docker-compose exec medialive-distributor netstat -an | grep :5000
```

### Environment Variables

```bash
# .env file
CONFIG_DIR=/app/config
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
```

### Port Reference

| Port(s)      | Protocol | Purpose           |
|--------------|----------|-------------------|
| 8000         | TCP      | Web UI / API      |
| 5000-5025    | UDP      | RTP Input         |
| User-defined | TCP/UDP  | SRT/RTMP Outputs  |

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-30  
**Maintained By:** Operations Team
