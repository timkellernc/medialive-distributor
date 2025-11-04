# Production Deployment Guide

## Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM
- Sufficient disk space for logs and data
- Open ports: 8080 (web), 5000-5100 (UDP), 8890-8990 (SRT)

## Quick Production Setup

### 1. Clone and Configure

```bash
git clone <your-repo>
cd stream-manager
cp .env.example .env
```

### 2. Edit Environment Variables

Edit `.env` file with production values:

```bash
# IMPORTANT: Change these security values!
SECRET_KEY=$(openssl rand -hex 32)
API_KEY=$(openssl rand -hex 32)

# Use PostgreSQL in production
DATABASE_URL=postgresql://streamuser:STRONG_PASSWORD@postgres:5432/streamdb
POSTGRES_PASSWORD=STRONG_PASSWORD
```

### 3. Enable PostgreSQL

Uncomment the PostgreSQL service in `docker-compose.yml`:

```yaml
services:
  postgres:
    # Uncomment this entire section
```

### 4. Start Services

```bash
docker-compose up -d
```

### 5. Verify Deployment

```bash
# Check all containers are running
docker-compose ps

# Check logs
docker-compose logs -f

# Test API
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8080/api/health
```

## Production Best Practices

### Security

1. **Change Default Credentials**
   - Update API_KEY in .env
   - Update SECRET_KEY in .env
   - Change PostgreSQL password

2. **Use HTTPS**
   - Deploy behind Nginx reverse proxy with SSL
   - Use Let's Encrypt for free SSL certificates

3. **Firewall Rules**
   ```bash
   # Allow only necessary ports
   ufw allow 80/tcp    # HTTP
   ufw allow 443/tcp   # HTTPS
   ufw allow 5000:5100/udp  # UDP inputs
   ufw allow 8890:8990/udp  # SRT
   ufw enable
   ```

4. **Restrict API Access**
   - Use strong API keys
   - Consider IP whitelisting
   - Implement rate limiting

### Nginx Reverse Proxy

Create `/etc/nginx/sites-available/stream-manager`:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket support
    location /socket.io/ {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable and test:
```bash
ln -s /etc/nginx/sites-available/stream-manager /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

### Monitoring

1. **Container Health**
   ```bash
   # Check container status
   docker-compose ps
   
   # View resource usage
   docker stats
   ```

2. **Application Logs**
   ```bash
   # Follow all logs
   docker-compose logs -f
   
   # View specific service
   docker-compose logs -f app
   ```

3. **System Metrics**
   - CPU usage should be < 80%
   - Memory usage should have headroom
   - Disk space should be monitored

### Backup Strategy

1. **Database Backups**
   ```bash
   # For PostgreSQL
   docker exec stream-manager-db pg_dump -U streamuser streamdb > backup_$(date +%Y%m%d).sql
   
   # For SQLite
   docker cp stream-manager-app:/data/stream_manager.db ./backup_$(date +%Y%m%d).db
   ```

2. **Automated Backups**
   Create a cron job:
   ```bash
   # Edit crontab
   crontab -e
   
   # Add daily backup at 2 AM
   0 2 * * * /path/to/backup-script.sh
   ```

3. **Configuration Backups**
   - Backup .env file
   - Backup docker-compose.yml
   - Version control your configuration

### Scaling

1. **Horizontal Scaling**
   - Run multiple app instances behind load balancer
   - Use external PostgreSQL database
   - Share MediaMTX instance

2. **Vertical Scaling**
   - Increase container resources in docker-compose.yml:
   ```yaml
   services:
     app:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 4G
   ```

### Updates and Maintenance

1. **Update Application**
   ```bash
   # Pull latest changes
   git pull
   
   # Rebuild and restart
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

2. **Database Migrations**
   ```bash
   # Run migrations (if using Alembic)
   docker-compose exec app alembic upgrade head
   ```

3. **Cleanup**
   ```bash
   # Remove old images
   docker image prune -a
   
   # Remove old logs
   docker-compose logs --tail=0 | wc -l
   ```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs app

# Check configuration
docker-compose config

# Verify port availability
netstat -tulpn | grep -E '8080|5000|8890'
```

### High CPU Usage

```bash
# Check FFmpeg processes
docker exec stream-manager-app ps aux | grep ffmpeg

# Monitor resource usage
docker stats

# Reduce concurrent outputs if needed
```

### Database Issues

```bash
# Connect to PostgreSQL
docker exec -it stream-manager-db psql -U streamuser -d streamdb

# Check tables
\dt

# Check connections
SELECT * FROM pg_stat_activity;
```

### MediaMTX Not Working

```bash
# Check MediaMTX logs
docker logs stream-manager-mediamtx

# Restart MediaMTX
docker restart stream-manager-mediamtx

# Verify configuration
docker exec stream-manager-mediamtx cat /config/mediamtx.yml
```

## Performance Tuning

### FFmpeg Optimization

Edit `app/services/ffmpeg_service.py` to add hardware acceleration:

```python
# For NVIDIA GPU
base_cmd = [
    'ffmpeg',
    '-hwaccel', 'cuda',
    '-hwaccel_output_format', 'cuda',
    ...
]

# For Intel Quick Sync
base_cmd = [
    'ffmpeg',
    '-hwaccel', 'qsv',
    ...
]
```

### Database Optimization

For PostgreSQL, adjust settings in docker-compose.yml:

```yaml
services:
  postgres:
    command: >
      postgres
      -c shared_buffers=256MB
      -c max_connections=200
      -c work_mem=16MB
```

## Monitoring Setup

### Prometheus + Grafana

Add to docker-compose.yml:

```yaml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## Support

For issues or questions:
- Check logs first: `docker-compose logs -f`
- Review API.md for API documentation
- Check GitHub issues
- Contact support team
