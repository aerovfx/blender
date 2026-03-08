# Blender Embedded Engine - Quick Start

## Bước 1: Cài Đặt Dependencies

```bash
cd /Users/pixibox/blender/blender-mcp
pip install -r requirements.txt
```

**Yêu cầu:**
- Python 3.11+
- Blender 4.0+
- aiohttp >= 3.9.0
- Pillow >= 10.0.0

---

## Bước 2: Chạy Embedded Engine

### Option A: Chạy trong Blender (Recommended)

```bash
# Mở Blender và chạy script
blender --background --python server/embedded_engine.py -- --port 8765
```

### Option B: Chạy với custom resolution

```bash
blender --background --python server/embedded_engine.py -- \
  --host 0.0.0.0 \
  --port 8765 \
  --width 1920 \
  --height 1080
```

### Option C: Chạy background (headless)

```bash
# macOS/Linux
nohup blender --background --python server/embedded_engine.py &

# Windows (PowerShell)
Start-Process blender -ArgumentList "--background","--python","server/embedded_engine.py","--","--port","8765"
```

---

## Bước 3: Truy Cập Web Interface

Mở trình duyệt:

```
http://localhost:8765
```

**Features:**
- 🖼️ Viewport streaming (auto-refresh 2s)
- 🎨 Create objects (cube, sphere, cylinder, etc.)
- 📊 Scene object list
- 📈 Statistics dashboard
- 📜 Activity log

---

## Bước 4: Test API

### Test với curl

```bash
# Get scene info
curl -X POST http://localhost:8765/api/command \
  -H "Content-Type: application/json" \
  -d '{"method": "get_scene_info"}'

# Create cube
curl -X POST http://localhost:8765/api/command \
  -H "Content-Type: application/json" \
  -d '{"method": "create_object", "params": {"type": "cube", "location": [0, 0, 0]}}'

# Render viewport
curl -X POST http://localhost:8765/api/command \
  -H "Content-Type: application/json" \
  -d '{"method": "render_viewport"}'
```

### Test với Python script

```bash
python examples/test_embedded_engine.py
```

### Test với WebSocket

```python
import websocket
import json

ws = websocket.create_connection("ws://localhost:8765/ws")

# Create object
ws.send(json.dumps({
    "method": "create_object",
    "params": {"type": "sphere", "location": [1, 2, 3]}
}))

# Get response
print(json.loads(ws.recv()))

# Render viewport
ws.send(json.dumps({
    "method": "render_viewport"
}))

# Get image (base64)
result = json.loads(ws.recv())
print(f"Image: {result['image'][:100]}...")

ws.close()
```

---

## Bước 5: API Reference

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/ws` | WebSocket | Real-time control |
| `/api/command` | POST | Execute command |
| `/api/viewport` | GET | Get viewport image |
| `/api/stats` | GET | Engine statistics |

### Available Commands

#### Create Object
```json
{
  "method": "create_object",
  "params": {
    "type": "cube",
    "location": [0, 0, 0],
    "rotation": [0, 0, 0],
    "scale": [1, 1, 1],
    "name": "MyCube"
  }
}
```

#### Modify Object
```json
{
  "method": "modify_object",
  "params": {
    "name": "MyCube",
    "location": [5, 0, 0],
    "rotation": [0, 45, 0],
    "scale": [2, 2, 2]
  }
}
```

#### Set Material
```json
{
  "method": "set_material",
  "params": {
    "object_name": "MyCube",
    "material_name": "RedMetal",
    "color": [1, 0, 0],
    "metallic": 1.0,
    "roughness": 0.2
  }
}
```

#### Render Viewport
```json
{
  "method": "render_viewport",
  "params": {
    "format": "PNG"
  }
}
```

#### Get Scene Info
```json
{
  "method": "get_scene_info"
}
```

---

## Bước 6: Integration Examples

### Python Client

```python
import requests

class BlenderClient:
    def __init__(self, base_url="http://localhost:8765"):
        self.base_url = base_url
    
    def create_object(self, type, **kwargs):
        return self._command("create_object", type=type, **kwargs)
    
    def render_viewport(self):
        return self._command("render_viewport")
    
    def _command(self, method, **params):
        response = requests.post(
            f"{self.base_url}/api/command",
            json={"method": method, "params": params}
        )
        return response.json()

# Usage
client = BlenderClient()
client.create_object("cube", location=[0, 0, 0])
client.create_object("sphere", location=[2, 0, 0])
viewport = client.render_viewport()
print(f"Rendered: {viewport['width']}x{viewport['height']}")
```

### JavaScript Client

```javascript
class BlenderClient {
    constructor(url = 'ws://localhost:8765/ws') {
        this.ws = new WebSocket(url);
    }

    async command(method, params = {}) {
        return new Promise((resolve) => {
            this.ws.send(JSON.stringify({ method, params }));
            this.ws.onmessage = (e) => {
                resolve(JSON.parse(e.data));
            };
        });
    }

    async createCube() {
        return await this.command('create_object', { type: 'cube' });
    }

    async render() {
        return await this.command('render_viewport');
    }
}

// Usage
const client = new BlenderClient();
await client.createCube();
const viewport = await client.render();
console.log(`Rendered: ${viewport.width}x${viewport.height}`);
```

---

## Troubleshooting

### Lỗi: "aiohttp not installed"

```bash
pip install aiohttp Pillow
```

### Lỗi: "Port already in use"

```bash
# Check port
lsof -i :8765

# Use different port
blender --background --python embedded_engine.py -- --port 8766
```

### Lỗi: "Off-screen setup failed"

Đây là warning, engine sẽ fallback về simple rendering.
Để fix, đảm bảo GPU drivers được cài đặt đúng.

### Web Interface không load

```bash
# Check server is running
curl http://localhost:8765/api/stats

# Check firewall
# macOS: System Preferences > Security > Firewall
# Windows: Windows Defender Firewall
```

---

## Next Steps

1. ✅ **Complete:** Chạy engine thành công
2. ⬜ **Tích hợp:** Nhúng viewport vào ứng dụng khác
3. ⬜ **Automation:** Tạo script tự động hóa workflow
4. ⬜ **Production:** Deploy với Docker/Kubernetes

---

## Tài Liệu Liên Quan

- [Full Documentation](blender_embedded_engine.md)
- [API Reference](docs/api.md)
- [Examples](examples/)

---

**🎉 Chúc mừng! Bạn đã chạy thành công Blender Embedded Engine!**
