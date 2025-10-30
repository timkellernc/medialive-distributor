# Quick Start Guide - MediaLive Distributor

## 5-Minute Setup

### 1. Deploy with Docker Compose

```bash
# Navigate to project directory
cd medialive-distributor

# Start the application
docker-compose up -d

# Verify it's running
docker-compose ps
curl http://localhost:8000/api/health
```

### 2. Open Web Interface

Open your browser to: **http://your-server-ip:8000**

### 3. Create Your First Channel

**In the Web UI:**
1. Click "Create Channel"
2. Fill in:
   - Name: `My First Channel`
   - RTP IP: Your server's IP (e.g., `192.168.1.100`)
   - RTP Port: `5000`
3. Click "Create Channel"

**Or via API:**
```bash
curl -X POST http://localhost:8000/api/channels \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Channel",
    "rtp_ip": "192.168.1.100",
    "rtp_port": 5000
  }'
```

### 4. Configure MediaLive

In AWS MediaLive Console:
1. Go to your channel → Output groups
2. Add UDP output group
3. Set destination: `rtp://your-distributor-ip:5000`
4. Enable SCTE-35 passthrough
5. Save and start channel

### 5. Add an Output

**In the Web UI:**
1. Click "Add Output" on your channel
2. Fill in:
   - Protocol: `SRT` or `RTMP`
   - URL: Your destination URL
3. Click "Add Output"

**Or via API:**
```bash
curl -X POST http://localhost:8000/api/channels/CHANNEL_ID/outputs \
  -H "Content-Type: application/json" \
  -d '{
    "protocol": "srt",
    "url": "srt://destination.com:9000?streamid=publish/stream"
  }'
```

### 6. Start the Channel

Click the **"Start"** button on your channel card.

✅ **You're live!** The stream will now be distributed to all your outputs.

---

## Common URLs

### SRT Examples
```
srt://cdn.example.com:9000?streamid=publish/mystream
srt://10.0.0.50:9000
srt://destination.com:9000?latency=2000
```

### RTMP Examples
```
rtmp://destination.com/live/streamkey
rtmps://live-api-s.facebook.com:443/rtmp/KEY
rtmp://a.rtmp.youtube.com/live2/KEY
```

---

## What's Next?

- **Add more outputs**: Click "Add Output" any time without interrupting the stream
- **Monitor status**: Watch real-time status, uptime, and errors in the dashboard
- **Add more channels**: Support for 25+ simultaneous channels
- **Read the docs**: Check out [README.md](README.md) for full documentation

---

## Troubleshooting

**Channel won't start?**
- Verify MediaLive is sending to the correct IP and port
- Check firewall allows UDP traffic on the RTP port
- View logs: `docker-compose logs -f`

**Output not connecting?**
- Verify the destination URL is correct
- Check network connectivity to the destination
- Look for error messages on the output card

**Need help?**
- Check [README.md](README.md) for detailed documentation
- Review [EXAMPLES.md](EXAMPLES.md) for common configurations
- See [DEPLOYMENT.md](DEPLOYMENT.md) for production setup

---

## System Requirements

- Docker & Docker Compose
- 10GbE network (for high channel counts)
- 4GB+ RAM
- Multi-core CPU

---

**Ready to scale?** This system supports 25+ channels with multiple outputs each!
