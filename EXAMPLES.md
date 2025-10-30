# Configuration Examples

## Example 1: Single Channel with Multiple Outputs

### Scenario
One MediaLive channel distributed to 3 SRT destinations and 2 RTMP destinations.

### API Configuration

```bash
# Create channel
curl -X POST http://localhost:8000/api/channels \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Main Event Channel",
    "rtp_ip": "192.168.1.100",
    "rtp_port": 5000
  }'

# Add SRT outputs
curl -X POST http://localhost:8000/api/channels/CHANNEL_ID/outputs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Primary CDN (SRT)",
    "protocol": "srt",
    "url": "srt://cdn1.example.com:9000?streamid=publish/main"
  }'

curl -X POST http://localhost:8000/api/channels/CHANNEL_ID/outputs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Backup CDN (SRT)",
    "protocol": "srt",
    "url": "srt://cdn2.example.com:9000?streamid=publish/main"
  }'

curl -X POST http://localhost:8000/api/channels/CHANNEL_ID/outputs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Archive Server (SRT)",
    "protocol": "srt",
    "url": "srt://10.0.10.50:9000?streamid=archive/main"
  }'

# Add RTMP outputs
curl -X POST http://localhost:8000/api/channels/CHANNEL_ID/outputs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "YouTube Live",
    "protocol": "rtmp",
    "url": "rtmp://a.rtmp.youtube.com/live2/YOUR_STREAM_KEY"
  }'

curl -X POST http://localhost:8000/api/channels/CHANNEL_ID/outputs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Facebook Live",
    "protocol": "rtmp",
    "url": "rtmps://live-api-s.facebook.com:443/rtmp/YOUR_STREAM_KEY"
  }'
```

### channels.json Result

```json
{
  "uuid-here": {
    "config": {
      "name": "Main Event Channel",
      "rtp_ip": "192.168.1.100",
      "rtp_port": 5000,
      "backup_rtp_ip": null,
      "backup_rtp_port": null,
      "outputs": [
        {
          "name": "Primary CDN (SRT)",
          "protocol": "srt",
          "url": "srt://cdn1.example.com:9000?streamid=publish/main",
          "enabled": true
        },
        {
          "name": "Backup CDN (SRT)",
          "protocol": "srt",
          "url": "srt://cdn2.example.com:9000?streamid=publish/main",
          "enabled": true
        },
        {
          "name": "Archive Server (SRT)",
          "protocol": "srt",
          "url": "srt://10.0.10.50:9000?streamid=archive/main",
          "enabled": true
        },
        {
          "name": "YouTube Live",
          "protocol": "rtmp",
          "url": "rtmp://a.rtmp.youtube.com/live2/YOUR_STREAM_KEY",
          "enabled": true
        },
        {
          "name": "Facebook Live",
          "protocol": "rtmp",
          "url": "rtmps://live-api-s.facebook.com:443/rtmp/YOUR_STREAM_KEY",
          "enabled": true
        }
      ]
    },
    "created_at": "2025-10-30T12:00:00"
  }
}
```

## Example 2: Multi-Channel Setup (Sports Events)

### Scenario
3 cameras, each as a separate channel, each distributed to multiple destinations.

```bash
# Channel 1: Main Camera
curl -X POST http://localhost:8000/api/channels \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Main Camera",
    "rtp_ip": "192.168.1.100",
    "rtp_port": 5000,
    "backup_rtp_ip": "192.168.1.101",
    "backup_rtp_port": 5000
  }'

# Channel 2: Close-up Camera
curl -X POST http://localhost:8000/api/channels \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Close-up Camera",
    "rtp_ip": "192.168.1.100",
    "rtp_port": 5001,
    "backup_rtp_ip": "192.168.1.101",
    "backup_rtp_port": 5001
  }'

# Channel 3: Wide Angle Camera
curl -X POST http://localhost:8000/api/channels \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Wide Angle Camera",
    "rtp_ip": "192.168.1.100",
    "rtp_port": 5002,
    "backup_rtp_ip": "192.168.1.101",
    "backup_rtp_port": 5002
  }'
```

## Example 3: SCTE-35 Ad Insertion Workflow

### Scenario
Channel with SCTE-35 markers for dynamic ad insertion.

```bash
# Create channel
curl -X POST http://localhost:8000/api/channels \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Live Stream with Ads",
    "rtp_ip": "192.168.1.100",
    "rtp_port": 5000
  }'

# SRT output to ad insertion server (preserves SCTE-35)
curl -X POST http://localhost:8000/api/channels/CHANNEL_ID/outputs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ad Insertion Server",
    "protocol": "srt",
    "url": "srt://ad-server.example.com:9000?streamid=input/channel1",
    "comment": "SCTE-35 markers will be preserved"
  }'

# RTMP output to social media (no SCTE-35 needed)
curl -X POST http://localhost:8000/api/channels/CHANNEL_ID/outputs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Social Media",
    "protocol": "rtmp",
    "url": "rtmp://social.example.com/live/stream1"
  }'
```

## Example 4: High Availability Setup

### Scenario
Dual redundant inputs with multiple outputs for mission-critical streaming.

```bash
# Create channel with backup RTP
curl -X POST http://localhost:8000/api/channels \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mission Critical Stream",
    "rtp_ip": "192.168.1.100",
    "rtp_port": 5000,
    "backup_rtp_ip": "192.168.1.101",
    "backup_rtp_port": 5000
  }'

# Primary CDN
curl -X POST http://localhost:8000/api/channels/CHANNEL_ID/outputs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Primary CDN East",
    "protocol": "srt",
    "url": "srt://cdn-east.example.com:9000?streamid=live/primary"
  }'

# Backup CDN (different region)
curl -X POST http://localhost:8000/api/channels/CHANNEL_ID/outputs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Backup CDN West",
    "protocol": "srt",
    "url": "srt://cdn-west.example.com:9000?streamid=live/primary"
  }'
```

## Example 5: Testing and Development

### Scenario
Local testing with SRT listener mode.

```bash
# Start local SRT receiver (in another terminal)
ffplay -fflags nobuffer srt://0.0.0.0:9000?mode=listener

# Create test channel
curl -X POST http://localhost:8000/api/channels \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Channel",
    "rtp_ip": "127.0.0.1",
    "rtp_port": 5000
  }'

# Add output to local SRT receiver
curl -X POST http://localhost:8000/api/channels/CHANNEL_ID/outputs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Local Test",
    "protocol": "srt",
    "url": "srt://127.0.0.1:9000"
  }'

# Generate test RTP stream (in another terminal)
ffmpeg -re -f lavfi -i testsrc=size=1280x720:rate=30 \
  -f lavfi -i sine=frequency=1000 \
  -c:v libx264 -preset ultrafast -b:v 2000k \
  -c:a aac -b:a 128k \
  -f rtp rtp://127.0.0.1:5000
```

## Example 6: Live Event Workflow

### Scenario
Pre-event setup, go live, add outputs during event, post-event teardown.

```bash
# === PRE-EVENT: Setup ===

# 1. Create channel
CHANNEL_ID=$(curl -s -X POST http://localhost:8000/api/channels \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Live Event 2025",
    "rtp_ip": "192.168.1.100",
    "rtp_port": 5000
  }' | jq -r '.id')

# 2. Add initial outputs
curl -X POST http://localhost:8000/api/channels/$CHANNEL_ID/outputs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Main CDN",
    "protocol": "srt",
    "url": "srt://cdn.example.com:9000?streamid=live/event2025"
  }'

# === GO LIVE ===

# 3. Start MediaLive channel (in AWS Console)
# 4. Start distributor channel
curl -X POST http://localhost:8000/api/channels/$CHANNEL_ID/start

# === DURING EVENT: Add social media outputs ===

# 5. Add YouTube (without interrupting existing outputs)
curl -X POST http://localhost:8000/api/channels/$CHANNEL_ID/outputs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "YouTube Live",
    "protocol": "rtmp",
    "url": "rtmp://a.rtmp.youtube.com/live2/YOUR_KEY"
  }'

# 6. Add Facebook
curl -X POST http://localhost:8000/api/channels/$CHANNEL_ID/outputs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Facebook Live",
    "protocol": "rtmp",
    "url": "rtmps://live-api-s.facebook.com:443/rtmp/YOUR_KEY"
  }'

# === POST-EVENT: Cleanup ===

# 7. Stop channel
curl -X POST http://localhost:8000/api/channels/$CHANNEL_ID/stop

# 8. Optional: Delete channel
curl -X DELETE http://localhost:8000/api/channels/$CHANNEL_ID
```

## SRT URL Options Reference

```bash
# Basic SRT URLs
srt://destination:port                                    # Caller mode (default)
srt://destination:port?mode=caller                        # Explicit caller
srt://0.0.0.0:port?mode=listener                         # Listener mode
srt://destination:port?mode=rendezvous                    # Rendezvous mode

# With Stream ID (recommended)
srt://destination:port?streamid=publish/mystream

# With latency
srt://destination:port?latency=1000                       # 1000ms latency

# With encryption
srt://destination:port?passphrase=mysecretkey&pbkeylen=16

# Combined options
srt://destination:port?streamid=live/ch1&latency=2000&passphrase=secret

# Listener with Stream ID
srt://0.0.0.0:9000?mode=listener&streamid=input/channel1
```

## RTMP URL Formats

```bash
# Standard RTMP
rtmp://server/app/streamkey

# RTMPS (secure)
rtmps://server:443/rtmp/streamkey

# Common platforms
rtmp://a.rtmp.youtube.com/live2/YOUR_STREAM_KEY
rtmps://live-api-s.facebook.com:443/rtmp/YOUR_STREAM_KEY
rtmp://live.twitch.tv/app/YOUR_STREAM_KEY
rtmp://rtmp.restream.io/live/YOUR_STREAM_KEY
```

## Bulk Operations with Scripts

### Create Multiple Channels

```bash
#!/bin/bash

# Create 10 channels
for i in {1..10}; do
  PORT=$((5000 + i - 1))
  curl -X POST http://localhost:8000/api/channels \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"Channel $i\",
      \"rtp_ip\": \"192.168.1.100\",
      \"rtp_port\": $PORT
    }"
  echo
done
```

### Add Same Output to All Channels

```bash
#!/bin/bash

# Get all channel IDs
CHANNEL_IDS=$(curl -s http://localhost:8000/api/channels | jq -r '.channels[].id')

# Add output to each
for CHANNEL_ID in $CHANNEL_IDS; do
  curl -X POST http://localhost:8000/api/channels/$CHANNEL_ID/outputs \
    -H "Content-Type: application/json" \
    -d '{
      "name": "Archive Server",
      "protocol": "srt",
      "url": "srt://archive.example.com:9000?streamid=channel-'$CHANNEL_ID'"
    }'
  echo
done
```

## Configuration File Template

Save this as `config/channels.json` for manual configuration:

```json
{
  "channel-uuid-1": {
    "config": {
      "name": "Channel 1",
      "rtp_ip": "192.168.1.100",
      "rtp_port": 5000,
      "backup_rtp_ip": null,
      "backup_rtp_port": null,
      "outputs": [
        {
          "name": "Output 1",
          "protocol": "srt",
          "url": "srt://destination:9000",
          "enabled": true
        }
      ]
    },
    "created_at": "2025-10-30T12:00:00"
  }
}
```

## Monitoring Script

```bash
#!/bin/bash
# watch-channels.sh - Monitor all channels

while true; do
  clear
  echo "=== MediaLive Distributor Status ==="
  echo
  curl -s http://localhost:8000/api/channels | jq -r '
    .channels[] | 
    "[\(.status | ascii_upcase)] \(.name) - \(.outputs | length) outputs"
  '
  echo
  sleep 5
done
```

Save and run:
```bash
chmod +x watch-channels.sh
./watch-channels.sh
```
