# MediaLive Distributor

Production-ready stream distribution system that receives RTP streams from AWS MediaLive and distributes to multiple SRT and RTMP outputs.

## Features

✅ **Multi-Channel Support** - Handle up to 25+ simultaneous channels  
✅ **Hot-Reload Outputs** - Add/remove outputs without interrupting others  
✅ **SCTE-35 Preservation** - Maintains SCTE-35 markers in SRT outputs  
✅ **Dual Input Support** - Optional backup RTP streams for redundancy  
✅ **Web Dashboard** - User-friendly interface for operators  
✅ **RESTful API** - Full programmatic control  
✅ **Real-time Monitoring** - WebSocket-based live status updates  
✅ **Zero Transcoding** - Pure remuxing for maximum efficiency  
✅ **Docker Deployment** - Containerized for easy deployment

## Architecture

```
MediaLive → RTP → [Distributor] → SRT (with SCTE-35)
                                 → RTMP
                                 → Multiple Outputs
```

The distributor receives RTP streams, converts them to MPEG-TS format, and distributes to multiple outputs without transcoding.

## System Requirements

- Docker & Docker Compose
- 10GbE network recommended for high channel counts
- CPU: Multi-core processor (Xeon Gold or equivalent)
- RAM: 4GB minimum, 8GB+ recommended for 25 channels
- Storage: Minimal (configuration only)

## Quick Start

### 1. Clone or Create Project Directory

```bash
mkdir medialive-distributor
cd medialive-distributor
```

### 2. Create Required Files

Ensure you have these files in your directory:
- `app.py` - Main application
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container configuration
- `docker-compose.yml` - Deployment configuration
- `static/index.html` - Web dashboard

### 3. Deploy

```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

### 4. Access Web Dashboard

Open your browser to: `http://your-server-ip:8000`

## Configuration

### Port Configuration

Edit `docker-compose.yml` to configure ports:

```yaml
ports:
  - "8000:8000"              # Web UI/API
  - "5000-5025:5000-5025/udp" # RTP input ports
```

### Host Networking (Recommended for Production)

For better performance and simpler port management:

```yaml
# In docker-compose.yml, replace ports section with:
network_mode: "host"
```

### Resource Limits

Adjust based on your channel count:

```yaml
deploy:
  resources:
    limits:
      cpus: '8.0'
      memory: 8G
```

## Usage Guide

### Creating a Channel

1. Click **"Create Channel"** button
2. Enter channel details:
   - **Name**: Descriptive name (e.g., "Main Event Stream")
   - **RTP IP**: IP address MediaLive sends to (usually server's IP)
   - **RTP Port**: Port number (e.g., 5000)
   - **Backup RTP** (optional): Redundant stream details
3. Click **"Create Channel"**

### Starting a Channel

1. Click **"Start"** button on the channel card
2. Wait for status to change to "running"
3. Monitor outputs for successful connections

### Adding Outputs

1. Click **"Add Output"** on a channel
2. Configure output:
   - **Name**: Optional (auto-generates if blank)
   - **Protocol**: SRT or RTMP
   - **URL**: Destination URL
3. Output starts immediately if channel is running

**SRT URL Examples:**
```
srt://destination.com:9000?streamid=publish/mystream
srt://10.0.0.50:9000?mode=caller
```

**RTMP URL Examples:**
```
rtmp://destination.com/live/streamkey
rtmp://10.0.0.50:1935/app/mystream
```

### Managing Outputs

- **Remove**: Click "Remove" button (doesn't affect other outputs)
- **View Status**: Real-time status, uptime, and error counts
- **Monitor Errors**: Error messages displayed on output cards

### Channel Status Indicators

- 🟢 **Running**: Channel active, receiving stream
- ⚪ **Stopped**: Channel configured but not started
- 🔴 **Error**: Channel encountered an error

## API Reference

### Base URL
```
http://your-server-ip:8000/api
```

### Endpoints

#### List All Channels
```http
GET /api/channels
```

Response:
```json
{
  "channels": [
    {
      "id": "uuid",
      "name": "Main Event",
      "rtp_ip": "192.168.1.100",
      "rtp_port": 5000,
      "status": "running",
      "uptime": 3600.5,
      "outputs": [...]
    }
  ]
}
```

#### Create Channel
```http
POST /api/channels
Content-Type: application/json

{
  "name": "New Channel",
  "rtp_ip": "192.168.1.100",
  "rtp_port": 5000,
  "backup_rtp_ip": "192.168.1.101",
  "backup_rtp_port": 5001,
  "outputs": []
}
```

#### Start Channel
```http
POST /api/channels/{channel_id}/start
```

#### Stop Channel
```http
POST /api/channels/{channel_id}/stop
```

#### Add Output
```http
POST /api/channels/{channel_id}/outputs
Content-Type: application/json

{
  "name": "Output 1",
  "protocol": "srt",
  "url": "srt://destination:9000?streamid=publish"
}
```

#### Remove Output
```http
DELETE /api/channels/{channel_id}/outputs/{output_id}
```

#### Delete Channel
```http
DELETE /api/channels/{channel_id}
```

### WebSocket

Real-time status updates:
```javascript
const ws = new WebSocket('ws://your-server-ip:8000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.channels);
};
```

## MediaLive Configuration

### Output Settings

Configure MediaLive to output to your distributor server:

1. **Output Group**: UDP/RTP
2. **Protocol**: RTP
3. **Destination**:
   - Primary: `rtp://your-distributor-ip:5000`
   - Backup: `rtp://your-distributor-ip:5001` (optional)
4. **SCTE-35**: Enable passthrough

### Recommended MediaLive Settings

- **Container**: MPEG-TS
- **Video Codec**: Copy or H.264
- **Audio Codec**: Copy or AAC
- **SCTE-35**: Passthrough enabled
- **PCR Period**: 20-100ms

## Monitoring & Troubleshooting

### View Logs

```bash
# All logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific timeframe
docker-compose logs --since=1h
```

### Common Issues

**Channel won't start:**
- Verify RTP port is not in use
- Check MediaLive is sending to correct IP/port
- Ensure firewall allows UDP traffic

**Output fails:**
- Verify destination URL is correct
- Check network connectivity to destination
- Review output error message in dashboard

**SCTE-35 not preserved:**
- Ensure MediaLive has SCTE-35 passthrough enabled
- Use SRT protocol (RTMP doesn't support SCTE-35)
- Verify receiving system supports SCTE-35 in MPEG-TS

**High CPU usage:**
- Check if transcoding is accidentally enabled
- Reduce number of concurrent outputs
- Verify proper FFmpeg remuxing (should be very low CPU)

### Performance Tuning

For 25 channels with multiple outputs each:

1. **Use host networking** for reduced overhead
2. **Allocate sufficient CPU cores** (2-4 per channel recommended)
3. **Monitor network bandwidth** (8Mbps × outputs × channels)
4. **Use SSD for configuration** storage
5. **Enable kernel UDP buffer tuning** if needed:

```bash
# Increase UDP receive buffer (Linux)
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.rmem_default=134217728
```

## Backup & Recovery

### Backup Configuration

```bash
# Backup configuration
cp -r config config-backup-$(date +%Y%m%d)

# Or use git
cd config && git init && git add . && git commit -m "backup"
```

### Restore Configuration

```bash
# Restore from backup
docker-compose down
cp -r config-backup-YYYYMMDD config
docker-compose up -d
```

### Configuration Location

Configuration is stored in: `./config/channels.json`

## Scaling

### Vertical Scaling

For more channels on one server:

1. Increase Docker resource limits in `docker-compose.yml`
2. Add more RTP port ranges
3. Monitor CPU/network usage

### Horizontal Scaling

For very large deployments:

1. Deploy multiple distributor instances
2. Route different channels to different instances
3. Use load balancer for web UI (optional)

## Security Considerations

- **Private Network**: Run on private network, no authentication by default
- **Firewall**: Restrict RTP ports to MediaLive IPs only
- **Web UI**: Use reverse proxy with HTTPS and auth if exposed
- **API**: Add authentication layer if needed

## Support & Maintenance

### Updating

```bash
# Pull latest code
git pull  # or update files manually

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Health Check

```bash
# Check container status
docker-compose ps

# Check application health
curl http://localhost:8000/api/health
```

## Technical Details

### FFmpeg Commands

**Receiver Process:**
```bash
ffmpeg -protocol_whitelist file,rtp,udp -i rtp://IP:PORT \
  -c copy -copyts -f mpegts -y /tmp/channel_ID.ts
```

**SRT Output:**
```bash
ffmpeg -i file:/tmp/channel_ID.ts -c copy -copyts \
  -f mpegts -mpegts_flags initial_discontinuity \
  -muxdelay 0 srt://destination
```

**RTMP Output:**
```bash
ffmpeg -i file:/tmp/channel_ID.ts -c copy -f flv rtmp://destination
```

### SCTE-35 Technical Notes

- Carried as MPEG-TS private sections (PID typically 0x86)
- Preserved through remuxing (`-c copy`)
- SRT maintains all MPEG-TS data including SCTE-35
- RTMP strips SCTE-35 (protocol limitation)

## License

MIT License - Use freely in production

## Contributing

Contributions welcome! Please test thoroughly before submitting PRs.

## Roadmap

- [ ] Automatic failover to backup RTP streams
- [ ] HLS output support
- [ ] Enhanced analytics and metrics
- [ ] Email/Slack alerts
- [ ] Output templates
- [ ] Bulk operations

---

**Built with:** Python, FastAPI, FFmpeg, Docker
