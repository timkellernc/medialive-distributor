# API Documentation

## Authentication

All API endpoints require authentication using an API key in the `X-API-Key` header.

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8080/api/health
```

## Base URL

```
http://localhost:8080/api
```

## Endpoints

### Health Check

**GET /health**

Check if the API is running.

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

### Inputs

#### List Inputs

**GET /inputs**

List all input streams.

Query Parameters:
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 100)

Response:
```json
[
  {
    "id": 1,
    "name": "Camera 1",
    "udp_port": 5001,
    "mediamtx_path": "camera_1",
    "srt_port": 8890,
    "status": "active",
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00",
    "output_count": 3
  }
]
```

#### Create Input

**POST /inputs**

Create a new input stream.

Request Body:
```json
{
  "name": "Camera 1",
  "udp_port": 5001  // Optional, auto-assigned if not provided
}
```

Response: Same as GET /inputs/{id}

#### Get Input

**GET /inputs/{id}**

Get details of a specific input including all outputs.

Response:
```json
{
  "id": 1,
  "name": "Camera 1",
  "udp_port": 5001,
  "mediamtx_path": "camera_1",
  "srt_port": 8890,
  "status": "active",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00",
  "output_count": 3,
  "outputs": [
    {
      "id": 1,
      "name": "YouTube",
      "protocol": "rtmp",
      "status": "running",
      ...
    }
  ]
}
```

#### Update Input

**PATCH /inputs/{id}**

Update an input stream.

Request Body:
```json
{
  "name": "Camera 1 Updated"
}
```

Response: Updated input object

#### Delete Input

**DELETE /inputs/{id}**

Delete an input and all its outputs.

Response:
```json
{
  "success": true,
  "message": "Input 1 deleted"
}
```

#### Get Input Status

**GET /inputs/{id}/status**

Get input status and statistics.

---

### Outputs

#### List Outputs

**GET /inputs/{input_id}/outputs**

List all outputs for an input.

#### Create Output

**POST /inputs/{input_id}/outputs**

Create a new output for an input.

Request Body:
```json
{
  "name": "YouTube Live",
  "url": "rtmp://a.rtmp.youtube.com/live2/your-stream-key",
  "protocol": "rtmp",
  "auto_reconnect": true,
  "reconnect_delay": 5
}
```

Protocol options:
- `srt_caller`: SRT in caller mode
- `srt_listener`: SRT in listener mode
- `rtmp`: RTMP streaming
- `udp`: UDP streaming
- `rtsp`: RTSP streaming

#### Get Output

**GET /inputs/{input_id}/outputs/{output_id}**

Get details of a specific output.

#### Update Output

**PATCH /inputs/{input_id}/outputs/{output_id}**

Update an output.

#### Delete Output

**DELETE /inputs/{input_id}/outputs/{output_id}**

Delete an output.

#### Start Output

**POST /inputs/{input_id}/outputs/{output_id}/start**

Start an output stream.

#### Stop Output

**POST /inputs/{input_id}/outputs/{output_id}/stop**

Stop an output stream.

#### Get Output Logs

**GET /inputs/{input_id}/outputs/{output_id}/logs**

Get logs for an output.

Query Parameters:
- `limit` (optional): Maximum logs to return (default: 100)

---

### System

#### System Status

**GET /system/status**

Get system health and statistics.

Response:
```json
{
  "healthy": true,
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "inputs_count": 5,
  "outputs_count": 15,
  "active_outputs": 12,
  "cpu_percent": 25.5,
  "memory_percent": 45.2,
  "mediamtx_healthy": true
}
```

#### MediaMTX Status

**GET /system/mediamtx/status**

Get MediaMTX status.

Response:
```json
{
  "healthy": true,
  "api_available": true,
  "paths_count": 5
}
```

---

## Error Responses

All endpoints may return the following error responses:

**400 Bad Request**
```json
{
  "detail": "Error message describing what went wrong"
}
```

**401 Unauthorized**
```json
{
  "detail": "Invalid API key"
}
```

**404 Not Found**
```json
{
  "detail": "Resource not found"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error"
}
```

## WebSocket Events

Connect to WebSocket at: `ws://localhost:8080/socket.io/`

### Client → Server Events

**subscribe_input**
```json
{
  "input_id": 1
}
```

**unsubscribe_input**
```json
{
  "input_id": 1
}
```

### Server → Client Events

**input_status_update**
```json
{
  "input_id": 1,
  "status": "active",
  "stats": {}
}
```

**output_status_update**
```json
{
  "input_id": 1,
  "output_id": 1,
  "status": "running",
  "stats": {}
}
```

**system_alert**
```json
{
  "type": "error",
  "message": "Alert message"
}
```
