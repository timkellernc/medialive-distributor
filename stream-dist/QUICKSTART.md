# Quick Start Guide

Get Stream Distribution Manager running in 5 minutes!

## Prerequisites

- Docker and Docker Compose installed
- 4GB+ RAM available
- Ports available: 8080, 5000-5100, 8890-8990

## Installation Steps

### 1. Start the Application

```bash
./start.sh
```

That's it! The script will:
- Create necessary directories
- Copy environment template
- Build Docker images
- Start all services

### 2. Access the Web UI

Open your browser and navigate to:
```
http://localhost:8080
```

### 3. Create Your First Input

1. Click "Add Input" button
2. Enter a name (e.g., "Camera 1")
3. Leave port blank for auto-assignment or enter specific port
4. Click "Create"

Your input is ready! Note the UDP port assigned.

### 4. Send a Test Stream

Using FFmpeg, send a test stream:

```bash
ffmpeg -re -i test_video.mp4 -c copy -f mpegts udp://localhost:5001
```

Replace `5001` with your assigned UDP port.

### 5. Add an Output

1. Click on your input stream
2. Click "Add Output"
3. Choose a protocol:
   - **RTMP**: For YouTube, Facebook, etc.
   - **SRT**: For reliable streaming
   - **UDP**: For local distribution
4. Enter destination URL:
   - RTMP: `rtmp://a.rtmp.youtube.com/live2/YOUR-STREAM-KEY`
   - SRT Caller: `srt://192.168.1.100:9000`
   - UDP: `udp://192.168.1.100:5000`
5. Click "Create"

The output will start automatically!

## Common Use Cases

### Streaming to YouTube

1. Get your stream key from YouTube Studio
2. Add RTMP output with URL:
   ```
   rtmp://a.rtmp.youtube.com/live2/YOUR-STREAM-KEY
   ```

### Streaming to Multiple Platforms

Simply add multiple outputs to the same input:
- YouTube (RTMP)
- Facebook (RTMP)
- Twitch (RTMP)
- Your CDN (SRT)

### Local Distribution

Use SRT or UDP outputs to send streams to local devices or servers.

## Monitoring

The dashboard shows real-time:
- Number of inputs
- Number of outputs
- Active outputs
- CPU usage

Individual outputs show:
- Running status
- Reconnection count
- Any errors

## Troubleshooting

### Output keeps reconnecting?

- Check destination is reachable
- Verify URL format is correct
- Check FFmpeg logs in UI

### Input shows no data?

- Verify stream is being sent to correct UDP port
- Check MediaMTX logs: `docker logs stream-manager-mediamtx`
- Test with: `ffmpeg -re -i test.mp4 -f mpegts udp://localhost:YOUR_PORT`

### Can't access web UI?

- Check containers are running: `docker-compose ps`
- Check logs: `docker-compose logs -f`
- Verify port 8080 is available: `netstat -tulpn | grep 8080`

## Next Steps

- Read [API.md](API.md) for API documentation
- See [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
- Check [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system

## Getting Help

- Check logs: `docker-compose logs -f`
- View system status: `http://localhost:8080/api/health`
- Review documentation files

## Stopping the Application

```bash
docker-compose down
```

To remove all data:
```bash
docker-compose down -v
```

---

**Happy Streaming! 🎥**
