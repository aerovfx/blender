# MCP Blender Server - API Documentation

## Overview

The Blender MCP Server provides two communication methods:

1. **MCP Stdio Transport** - For LLM integration (Claude Desktop, etc.)
2. **WebSocket Transport** - For web clients and custom applications

---

## MCP Stdio Transport

### Configuration for Claude Desktop

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "blender": {
      "command": "blender",
      "args": [
        "--background",
        "--python",
        "/path/to/blender-mcp/server/mcp_server.py"
      ]
    }
  }
}
```

### Available Tools

#### 1. create_object

Create a 3D primitive object.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| type | string | Yes | Object type: cube, sphere, cylinder, cone, torus, plane, light, camera |
| location | array[3] | No | Position [x, y, z] |
| rotation | array[3] | No | Rotation in degrees [x, y, z] |
| scale | array[3] | No | Scale [x, y, z] |
| name | string | No | Object name |
| radius | number | No | Radius for spheres, cylinders |
| depth | number | No | Height for cylinders, cones |
| energy | number | No | Light energy (for light type) |
| color | array[3] | No | Color [r, g, b] |

**Example:**
```json
{
  "type": "create_object",
  "arguments": {
    "type": "cube",
    "location": [0, 0, 0],
    "name": "MyCube"
  }
}
```

#### 2. delete_object

Delete an object from the scene.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Object name |

#### 3. get_scene_info

Get information about the current scene.

**Parameters:** None

**Returns:**
```json
{
  "scene_name": "Scene",
  "frame_current": 1,
  "objects": [...],
  "object_count": 5,
  "render_engine": "CYCLES"
}
```

#### 4. get_object_info

Get detailed information about an object.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Object name |

#### 5. modify_object

Modify an object's transform.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Object name |
| location | array[3] | No | New position |
| rotation | array[3] | No | New rotation (degrees) |
| scale | array[3] | No | New scale |

#### 6. set_material

Create or apply a material.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| object_name | string | Yes | Target object |
| material_name | string | Yes | Material name |
| color | array[4] | No | Base color [r, g, b, a] |
| metallic | number | No | 0-1 |
| roughness | number | No | 0-1 |

#### 7. create_camera

Add a camera to the scene.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| location | array[3] | No | Camera position |
| rotation | array[3] | No | Camera rotation |
| name | string | No | Camera name |
| focal_length | number | No | Focal length (mm) |

#### 8. create_light

Add a light source.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| type | string | Yes | POINT, SUN, SPOT, AREA |
| location | array[3] | No | Light position |
| energy | number | No | Light energy |
| color | array[3] | No | Light color |
| name | string | No | Light name |

#### 9. render_scene

Render the current scene.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| filepath | string | No | Output path |
| resolution_x | integer | No | Width |
| resolution_y | integer | No | Height |
| samples | integer | No | Render samples |

#### 10. export_file

Export scene to file.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| filepath | string | Yes | Output path |
| format | string | Yes | FBX, OBJ, GLTF, STL, PLY |
| use_selection | boolean | No | Export selected only |

#### 11. clear_scene

Remove all objects (DANGEROUS).

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| confirm | boolean | Yes | Must be true |

---

## WebSocket Transport

### Connection

```
ws://localhost:8765
```

### Message Format

**Request:**
```json
{
  "type": "request",
  "id": 1,
  "method": "create_object",
  "params": {
    "type": "cube",
    "location": [0, 0, 0]
  }
}
```

**Response:**
```json
{
  "type": "response",
  "id": 1,
  "result": {
    "success": true,
    "object_name": "Cube"
  }
}
```

### Message Types

| Type | Description |
|------|-------------|
| `request` | Tool execution request |
| `response` | Tool execution response |
| `ping` | Connection test |
| `pong` | Ping response |
| `auth` | Authentication request |
| `auth_success` | Authentication successful |
| `auth_failed` | Authentication failed |
| `error` | Error response |

### Authentication

If authentication is required, send first:

```json
{
  "type": "auth",
  "params": {
    "api_key": "your-api-key"
  }
}
```

### JavaScript Example

```javascript
const ws = new WebSocket('ws://localhost:8765');

ws.onopen = () => {
  console.log('Connected to Blender');
  
  // Create a cube
  ws.send(JSON.stringify({
    type: 'request',
    id: 1,
    method: 'create_object',
    params: {
      type: 'cube',
      location: [0, 0, 0]
    }
  }));
};

ws.onmessage = (event) => {
  const response = JSON.parse(event.data);
  console.log('Response:', response);
};
```

### Python Example

```python
import websocket
import json

ws = websocket.create_connection("ws://localhost:8765")

# Wait for welcome message
welcome = json.loads(ws.recv())
print("Welcome:", welcome)

# Create object
ws.send(json.dumps({
    "type": "request",
    "id": 1,
    "method": "create_object",
    "params": {
        "type": "sphere",
        "location": [1, 2, 3]
    }
}))

# Get response
response = json.loads(ws.recv())
print("Response:", response)

ws.close()
```

---

## Security

### API Key Authentication

Generate or provide an API key when starting the server:

```bash
# Auto-generate API key
blender --background --python websocket_server.py -- --require-auth

# Provide custom API key
blender --background --python websocket_server.py -- --api-key my-secret-key
```

### Rate Limiting

Default: 100 requests per minute per client.

Configure with `--rate-limit`:

```bash
blender --background --python websocket_server.py -- --rate-limit 200
```

### Command Whitelist

Restrict available commands:

```bash
blender --background --python websocket_server.py -- \
  --allowed-commands create_object get_scene_info modify_object
```

---

## Error Handling

### Error Response Format

```json
{
  "type": "error",
  "id": 1,
  "error": "Object not found: Cube"
}
```

### Common Errors

| Error | Description |
|-------|-------------|
| `Object not found` | Specified object doesn't exist |
| `Unknown method` | Invalid tool name |
| `Authentication required` | Auth needed but not provided |
| `Rate limit exceeded` | Too many requests |
| `Command not allowed` | Command not in whitelist |

---

## Best Practices

1. **Always check responses** for success/error status
2. **Use meaningful object names** for easier reference
3. **Batch operations** when possible to reduce round-trips
4. **Handle errors gracefully** in your client code
5. **Use authentication** in production environments
6. **Monitor rate limits** to avoid being blocked
