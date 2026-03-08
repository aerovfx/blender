# Blender Embedded Engine Guide

**Chạy Blender UI như một Engine - Nhúng Blender vào ứng dụng khác**

Hướng dẫn này mô tả cách chạy Blender như một engine với khả năng điều khiển từ xa, tương tự như Omnistep hoặc các hệ thống render pipeline.

---

## 🎯 Mục Tiêu

Biến Blender thành một **engine service** có thể:
- 🖥️ Chạy như background service với UI nhúng
- 🔌 Điều khiển từ xa qua API/WebSocket
- 📊 Hiển thị viewport trong ứng dụng khác
- ⚡ Xử lý rendering tự động
- 🔄 Integration với pipeline production

---

## 📋 Yêu Cầu Hệ Thống

### Tối Thiểu
- **Blender:** 4.0+
- **Python:** 3.11+
- **OS:** Windows 10/11, macOS 12+, Linux
- **RAM:** 16GB+
- **GPU:** NVIDIA/AMD với OpenGL 4.5+

### Khuyến Nghị
- **GPU:** NVIDIA RTX 3060+ hoặc AMD RX 6700+
- **RAM:** 32GB+
- **Storage:** NVMe SSD

---

## 1. Kiến Trúc Tổng Quan

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Application                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Web App     │  │ Desktop App │  │ Mobile App          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/WebSocket
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Blender Embedded Engine                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Headless/Headed Mode Switch                         │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Embedded Viewport (Off-screen Rendering)            │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Python API Server (bpy)                             │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Render Engine (Cycles/Eevee)                        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Output Layer                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Images      │  │ Video       │  │ 3D Assets (FBX)     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Chế Độ Chạy Blender

### 2.1 Headless Mode (Background)

Chạy không có UI, tối ưu cho server/render farm:

```bash
# Basic headless
blender --background --python script.py

# With specific scene
blender background_file.blend --background --python script.py

# Multiple operations
blender --background file.blend \
  --python script1.py \
  --python script2.py \
  --python-expr "bpy.ops.render.render()"
```

### 2.2 Headed Mode với Off-screen Rendering

Chạy có UI nhưng render off-screen:

```bash
# Off-screen rendering (no display required)
blender --background --python-offscreen --python script.py

# macOS specific
blender --background --python-expr "
import bpy
bpy.context.preferences.system.offscreen_samples = 8
"
```

### 2.3 Embedded UI Mode

Nhúng viewport Blender vào ứng dụng khác:

```python
#!/usr/bin/env python3
"""
Embedded Blender Viewport Example
"""

import bpy
import gpu
from gpu_extras.batch import batch_for_shader

# Enable off-screen rendering
bpy.context.preferences.system.offscreen_samples = 4

# Create custom viewport
def draw_offscreen():
    """Render viewport to texture"""
    scene = bpy.context.scene
    view_layer = bpy.context.view_layer
    
    # Setup off-screen buffer
    width = 1920
    height = 1080
    
    # Create framebuffer
    offscreen = gpu.types.GPUOffScreen(width, height)
    
    with offscreen.bind():
        # Render scene
        view_layer.update()
        bpy.context.scene.render.engine = 'CYCLES'
        
    # Get pixel data
    buffer = offscreen.color_texture
    pixels = gpu.types.Buffer('BYTE', width * height * 4, buffer)
    
    return pixels, width, height

# Usage
pixels, width, height = draw_offscreen()
```

---

## 3. Remote Control API

### 3.1 WebSocket Server với Viewport Streaming

```python
#!/usr/bin/env python3
"""
Blender Embedded Engine with Viewport Streaming
"""

import bpy
import asyncio
import json
import base64
from aiohttp import web
import gpu
from gpu_extras.batch import batch_for_shader


class BlenderEngine:
    """Blender as embedded engine"""

    def __init__(self, width=1920, height=1080):
        self.width = width
        self.height = height
        self.offscreen = None
        self.setup_offscreen()

    def setup_offscreen(self):
        """Setup off-screen rendering context"""
        self.offscreen = gpu.types.GPUOffScreen(self.width, self.height)

    def render_viewport(self) -> bytes:
        """Render current viewport to image bytes"""
        with self.offscreen.bind():
            # Clear buffer
            gpu.state.blend_set('ALPHA')
            gpu.state.depth_test_set('LESS')
            
            # Render scene
            bpy.context.view_layer.update()
            
            # Read pixels
            buffer = self.offscreen.color_texture
            pixels = gpu.types.Buffer('BYTE', self.width * self.height * 4, buffer)
        
        return bytes(pixels)

    def render_final(self, filepath: str) -> dict:
        """Final render with Cycles/Eevee"""
        scene = bpy.context.scene
        
        # Configure render
        scene.render.engine = 'CYCLES'
        scene.render.filepath = filepath
        scene.render.resolution_x = self.width
        scene.render.resolution_y = self.height
        
        # Render
        bpy.ops.render.render(write_still=True)
        
        return {
            "success": True,
            "filepath": filepath,
            "samples": scene.cycles.samples
        }

    def execute_command(self, command: dict) -> dict:
        """Execute Blender command"""
        method = command.get("method")
        params = command.get("params", {})
        
        commands = {
            "create_object": self.create_object,
            "modify_object": self.modify_object,
            "set_material": self.set_material,
            "render_viewport": self.render_viewport_command,
            "render_final": self.render_final_command,
            "get_scene_info": self.get_scene_info,
        }
        
        if method in commands:
            return commands[method](**params)
        else:
            return {"error": f"Unknown method: {method}"}

    def create_object(self, type: str, location=None, **kwargs):
        """Create 3D object"""
        if location:
            bpy.ops.mesh.primitive_cube_add(location=location)
        else:
            bpy.ops.mesh.primitive_cube_add()
        
        obj = bpy.context.active_object
        return {"success": True, "object": obj.name}

    def modify_object(self, name: str, **transforms):
        """Modify object transform"""
        obj = bpy.data.objects.get(name)
        if not obj:
            return {"error": f"Object not found: {name}"}
        
        if "location" in transforms:
            obj.location = transforms["location"]
        if "rotation" in transforms:
            obj.rotation_euler = transforms["rotation"]
        if "scale" in transforms:
            obj.scale = transforms["scale"]
        
        return {"success": True, "object": name}

    def set_material(self, object_name: str, **mat_params):
        """Set material on object"""
        # Implementation for material setup
        return {"success": True}

    def render_viewport_command(self) -> dict:
        """Render viewport and return as base64"""
        import io
        from PIL import Image
        
        pixels = self.render_viewport()
        
        # Convert to image
        img = Image.new('RGBA', (self.width, self.height))
        img.frombytes(pixels)
        
        # Encode to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            "success": True,
            "image": f"data:image/png;base64,{img_base64}",
            "width": self.width,
            "height": self.height
        }

    def render_final_command(self, filepath: str) -> dict:
        """Final render command"""
        return self.render_final(filepath)

    def get_scene_info(self) -> dict:
        """Get scene information"""
        objects = [
            {
                "name": obj.name,
                "type": obj.type,
                "location": list(obj.location),
            }
            for obj in bpy.context.scene.objects
        ]
        
        return {
            "scene": bpy.context.scene.name,
            "frame": bpy.context.scene.frame_current,
            "objects": objects
        }


# HTTP WebSocket Server
class EngineServer:
    """WebSocket server for Blender Engine"""

    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.engine = BlenderEngine()
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/ws', self.handle_websocket)
        self.app.router.add_post('/api/command', self.handle_api)
        self.app.router.add_get('/api/viewport', self.handle_viewport)

    async def handle_index(self, request):
        """Serve web interface"""
        return web.Response(text="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Blender Embedded Engine</title>
            <style>
                body { background: #1a1a2e; color: white; font-family: sans-serif; }
                #viewport { width: 1920px; height: 1080px; background: #000; }
                .controls { margin: 20px; }
                button { padding: 10px 20px; margin: 5px; }
            </style>
        </head>
        <body>
            <h1>🎬 Blender Embedded Engine</h1>
            <div class="controls">
                <button onclick="createCube()">Create Cube</button>
                <button onclick="renderViewport()">Render Viewport</button>
                <button onclick="renderFinal()">Final Render</button>
            </div>
            <canvas id="viewport"></canvas>
            <script>
                const ws = new WebSocket('ws://' + window.location.host + '/ws');
                
                function createCube() {
                    ws.send(JSON.stringify({
                        method: 'create_object',
                        params: { type: 'cube' }
                    }));
                }
                
                function renderViewport() {
                    fetch('/api/viewport')
                        .then(r => r.json())
                        .then(data => {
                            const img = new Image();
                            img.src = data.image;
                            document.body.appendChild(img);
                        });
                }
                
                ws.onmessage = (e) => {
                    console.log('Message:', e.data);
                };
            </script>
        </body>
        </html>
        """, content_type='text/html')

    async def handle_websocket(self, request):
        """WebSocket handler"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                command = json.loads(msg.data)
                result = self.engine.execute_command(command)
                await ws.send_json(result)

        return ws

    async def handle_api(self, request):
        """REST API handler"""
        command = await request.json()
        result = self.engine.execute_command(command)
        return web.json_response(result)

    async def handle_viewport(self, request):
        """Viewport streaming"""
        result = self.engine.render_viewport_command()
        return web.json_response(result)

    def run(self):
        """Start server"""
        print(f"🚀 Blender Embedded Engine")
        print(f"📍 http://{self.host}:{self.port}")
        print(f"🔌 WebSocket: ws://{self.host}:{self.port}/ws")
        
        web.run_app(self.app, host=self.host, port=self.port)


if __name__ == '__main__':
    server = EngineServer()
    server.run()
```

---

## 4. Nhúng Viewport vào Ứng Dụng

### 4.1 Electron App Integration

```javascript
// main.js - Electron App
const { app, BrowserWindow, ipcMain } = require('electron');
const WebSocket = require('ws');

let mainWindow;
let blenderWS;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1920,
        height: 1080,
        webPreferences: {
            nodeIntegration: true
        }
    });

    mainWindow.loadFile('index.html');

    // Connect to Blender
    blenderWS = new WebSocket('ws://localhost:8765/ws');

    blenderWS.on('message', (data) => {
        const result = JSON.parse(data);
        mainWindow.webContents.send('blender-update', result);
    });
}

ipcMain.handle('blender-command', async (event, command) => {
    return new Promise((resolve) => {
        blenderWS.send(JSON.stringify(command));
        blenderWS.once('message', (data) => {
            resolve(JSON.parse(data));
        });
    });
});

app.whenReady().then(createWindow);
```

```html
<!-- index.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Blender Embedded</title>
    <style>
        #viewport {
            width: 100%;
            height: 600px;
            background: #000;
        }
        .toolbar {
            padding: 10px;
            background: #333;
        }
    </style>
</head>
<body>
    <div class="toolbar">
        <button onclick="createCube()">📦 Cube</button>
        <button onclick="createSphere()">🔮 Sphere</button>
        <button onclick="render()">🎬 Render</button>
    </div>
    <img id="viewport" />
    
    <script>
        const { ipcRenderer } = require('electron');
        
        async function createCube() {
            const result = await ipcRenderer.invoke('blender-command', {
                method: 'create_object',
                params: { type: 'cube' }
            });
            console.log(result);
        }
        
        async function render() {
            const result = await ipcRenderer.invoke('blender-command', {
                method: 'render_viewport'
            });
            document.getElementById('viewport').src = result.image;
        }
        
        ipcRenderer.on('blender-update', (event, data) => {
            console.log('Blender update:', data);
        });
    </script>
</body>
</html>
```

### 4.2 Web Browser Integration (WebGL Streaming)

```python
#!/usr/bin/env python3
"""
Stream Blender viewport to web browser via WebGL
"""

import bpy
import asyncio
from aiohttp import web
import json
import base64


class ViewportStreamer:
    """Stream Blender viewport to web clients"""

    def __init__(self):
        self.clients = set()
        self.fps = 24
        self.width = 1280
        self.height = 720

    async def stream_handler(self, request):
        """WebSocket stream handler"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.clients.add(ws)

        try:
            while True:
                # Render frame
                frame_data = self.render_frame()
                
                # Send to all clients
                await ws.send_json({
                    "type": "frame",
                    "data": frame_data,
                    "frame": bpy.context.scene.frame_current
                })
                
                # Next frame
                bpy.context.scene.frame_set(bpy.context.scene.frame_current + 1)
                
                # Control FPS
                await asyncio.sleep(1.0 / self.fps)
        except:
            pass
        finally:
            self.clients.remove(ws)

        return ws

    def render_frame(self) -> str:
        """Render current frame to base64"""
        # Implementation for frame rendering
        pass

    def create_app(self):
        """Create web application"""
        app = web.Application()
        app.router.add_get('/stream', self.stream_handler)
        app.router.add_get('/', self.handle_index)
        return app

    def handle_index(self, request):
        """Serve web player"""
        return web.Response(text="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Blender Viewport Stream</title>
            <style>
                #stream { width: 100%; max-width: 1280px; }
            </style>
        </head>
        <body>
            <h1>🎬 Blender Live Viewport</h1>
            <img id="stream" />
            <script>
                const ws = new WebSocket('ws://' + window.location.host + '/stream');
                const img = document.getElementById('stream');
                
                ws.onmessage = (e) => {
                    const data = JSON.parse(e.data);
                    if (data.type === 'frame') {
                        img.src = 'data:image/jpeg;base64,' + data.data;
                    }
                };
            </script>
        </body>
        </html>
        """, content_type='text/html')


if __name__ == '__main__':
    from aiohttp import web
    streamer = ViewportStreamer()
    web.run_app(streamer.create_app(), port=8080)
```

---

## 5. Render Pipeline Automation

### 5.1 Batch Render System

```python
#!/usr/bin/env python3
"""
Automated Render Pipeline
"""

import bpy
import os
import json
from pathlib import Path
from datetime import datetime


class RenderPipeline:
    """Automated render pipeline for production"""

    def __init__(self, output_dir: str = "//renders"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.scenes = []
        self.render_queue = []

    def add_scene(self, scene_name: str, frames: range, **kwargs):
        """Add scene to render queue"""
        self.render_queue.append({
            "scene": scene_name,
            "frames": list(frames),
            "resolution": kwargs.get("resolution", (1920, 1080)),
            "samples": kwargs.get("samples", 128),
            "engine": kwargs.get("engine", "CYCLES")
        })

    def render_scene(self, scene_name: str, frame: int, **config) -> dict:
        """Render single frame"""
        scene = bpy.data.scenes.get(scene_name)
        if not scene:
            return {"error": f"Scene not found: {scene_name}"}

        # Configure render
        scene.render.engine = config.get("engine", "CYCLES")
        scene.render.resolution_x = config.get("resolution", (1920, 1080))[0]
        scene.render.resolution_y = config.get("resolution", (1920, 1080))[1]
        scene.cycles.samples = config.get("samples", 128)
        scene.frame_set(frame)

        # Output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"{scene_name}_{frame:04d}_{timestamp}.png"
        scene.render.filepath = str(output_path)

        # Render
        bpy.ops.render.render(write_still=True)

        return {
            "success": True,
            "scene": scene_name,
            "frame": frame,
            "output": str(output_path)
        }

    def render_all(self) -> list:
        """Render all scenes in queue"""
        results = []

        for scene_config in self.render_queue:
            for frame in scene_config["frames"]:
                result = self.render_scene(
                    scene_config["scene"],
                    frame,
                    resolution=scene_config["resolution"],
                    samples=scene_config["samples"]
                )
                results.append(result)

        return results

    def export_report(self, results: list, filepath: str):
        """Export render report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_frames": len(results),
            "successful": sum(1 for r in results if r.get("success")),
            "failed": sum(1 for r in results if not r.get("success")),
            "outputs": [r.get("output") for r in results if r.get("success")]
        }

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)

        return report


# Usage
if __name__ == '__main__':
    pipeline = RenderPipeline()

    # Add scenes
    pipeline.add_scene("Scene", range(1, 100), resolution=(1920, 1080), samples=256)
    pipeline.add_scene("Scene_2", range(1, 50), resolution=(3840, 2160), samples=512)

    # Render all
    results = pipeline.render_all()

    # Export report
    report = pipeline.export_report(results, "render_report.json")
    print(f"Rendered {report['successful']} frames")
```

### 5.2 Distributed Rendering

```python
#!/usr/bin/env python3
"""
Distributed Render Farm Controller
"""

import bpy
import asyncio
import aiohttp
from typing import List, Dict


class RenderFarm:
    """Distributed render farm controller"""

    def __init__(self, workers: List[str]):
        """
        Args:
            workers: List of worker URLs
        """
        self.workers = workers
        self.task_queue = asyncio.Queue()
        self.results = []

    async def submit_task(self, scene: str, frame: int, priority: int = 0):
        """Submit render task"""
        await self.task_queue.put({
            "scene": scene,
            "frame": frame,
            "priority": priority,
            "timestamp": asyncio.get_event_loop().time()
        })

    async def worker_client(self, worker_url: str, session: aiohttp.ClientSession):
        """Worker client coroutine"""
        while True:
            try:
                # Get task from queue
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)

                # Send to worker
                async with session.post(
                    f"{worker_url}/render",
                    json=task
                ) as response:
                    result = await response.json()
                    self.results.append(result)

                self.task_queue.task_done()

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Worker {worker_url} error: {e}")

    async def run(self):
        """Start render farm"""
        async with aiohttp.ClientSession() as session:
            # Start workers
            workers = [
                asyncio.create_task(self.worker_client(url, session))
                for url in self.workers
            ]

            # Wait for all tasks
            await self.task_queue.join()

            # Cancel workers
            for w in workers:
                w.cancel()

        return self.results


# Usage
async def main():
    farm = RenderFarm([
        "http://worker1:8080",
        "http://worker2:8080",
        "http://worker3:8080"
    ])

    # Submit frames
    for frame in range(1, 100):
        await farm.submit_task("MainScene", frame)

    # Render
    results = await farm.run()
    print(f"Rendered {len(results)} frames")

# asyncio.run(main())
```

---

## 6. Production Integration

### 6.1 Docker Container

```dockerfile
# Dockerfile for Blender Engine
FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    libgl1-mesa-glx \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Install Blender
RUN wget https://download.blender.org/release/Blender4.0/blender-4.0.0-linux-x64.tar.xz \
    && tar -xf blender-4.0.0-linux-x64.tar.xz \
    && mv blender-4.0.0-linux-x64 /opt/blender \
    && ln -s /opt/blender/blender /usr/local/bin/blender

# Install Python dependencies
COPY requirements.txt /app/
RUN pip3 install -r /app/requirements.txt

# Copy application
COPY . /app/
WORKDIR /app

# Expose ports
EXPOSE 8765 8080

# Run
CMD ["python3", "server/websocket_server.py", "--host", "0.0.0.0"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  blender-engine:
    build: .
    ports:
      - "8765:8765"
      - "8080:8080"
    volumes:
      - ./projects:/app/projects
      - ./renders:/app/renders
    environment:
      - BLENDER_USER_CONFIG=/app/config
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  web-ui:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./web_interface:/usr/share/nginx/html
```

### 6.2 Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: blender-engine
spec:
  replicas: 3
  selector:
    matchLabels:
      app: blender-engine
  template:
    metadata:
      labels:
        app: blender-engine
    spec:
      containers:
      - name: blender
        image: your-registry/blender-engine:latest
        ports:
        - containerPort: 8765
        resources:
          requests:
            nvidia.com/gpu: 1
          limits:
            nvidia.com/gpu: 1
            memory: "16Gi"
            cpu: "4"
        volumeMounts:
        - name: projects
          mountPath: /app/projects
        - name: renders
          mountPath: /app/renders
      volumes:
      - name: projects
        persistentVolumeClaim:
          claimName: projects-pvc
      - name: renders
        persistentVolumeClaim:
          claimName: renders-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: blender-service
spec:
  selector:
    app: blender-engine
  ports:
  - port: 8765
    targetPort: 8765
  type: LoadBalancer
```

---

## 7. Performance Optimization

### 7.1 GPU Optimization

```python
# GPU settings for optimal performance
import bpy

# Cycles settings
scene = bpy.context.scene
scene.cycles.device = 'GPU'
scene.cycles.samples = 128
scene.cycles.use_denoising = True

# GPU device
preferences = bpy.context.preferences
cycles_prefs = preferences.addons['cycles'].preferences
cycles_prefs.compute_device_type = 'CUDA'  # or 'HIP', 'METAL'

# Enable all GPUs
for device in cycles_prefs.devices:
    device.use = True
```

### 7.2 Memory Management

```python
# Memory optimization
import bpy

# Clear unused data
for block in bpy.data.meshes:
    if block.users == 0:
        bpy.data.meshes.remove(block)

for block in bpy.data.materials:
    if block.users == 0:
        bpy.data.materials.remove(block)

for block in bpy.data.images:
    if block.users == 0:
        bpy.data.images.remove(block)

# Garbage collection
import gc
gc.collect()
```

---

## 8. Security Considerations

### 8.1 API Security

```python
# Secure API with authentication
from aiohttp import web
import secrets

class SecureEngine:
    def __init__(self):
        self.api_key = secrets.token_urlsafe(32)
        self.rate_limits = {}

    async def authenticate(self, request):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != self.api_key:
            raise web.HTTPUnauthorized()

    async def rate_limit(self, client_id: str, limit: int = 100):
        import time
        now = time.time()
        
        if client_id not in self.rate_limits:
            self.rate_limits[client_id] = []
        
        # Clean old requests
        self.rate_limits[client_id] = [
            t for t in self.rate_limits[client_id]
            if now - t < 60
        ]
        
        if len(self.rate_limits[client_id]) >= limit:
            raise web.HTTPTooManyRequests()
        
        self.rate_limits[client_id].append(now)
```

---

## 9. Monitoring & Logging

```python
#!/usr/bin/env python3
"""
Monitoring and Logging for Blender Engine
"""

import logging
import asyncio
from datetime import datetime
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
RENDER_COUNTER = Counter('blender_renders_total', 'Total renders')
RENDER_DURATION = Histogram('blender_render_duration_seconds', 'Render duration')
ERROR_COUNTER = Counter('blender_errors_total', 'Total errors')

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('blender_engine.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('BlenderEngine')


class MonitoredEngine:
    """Engine with monitoring"""

    def __init__(self):
        self.logger = logger
        self.start_time = datetime.now()

    @RENDER_DURATION.time()
    def render(self, scene: str, frame: int):
        """Render with metrics"""
        RENDER_COUNTER.inc()
        self.logger.info(f"Rendering {scene} frame {frame}")
        
        try:
            # Render implementation
            pass
        except Exception as e:
            ERROR_COUNTER.inc()
            self.logger.error(f"Render failed: {e}")
            raise

    def get_metrics(self):
        """Get Prometheus metrics"""
        return {
            "uptime": (datetime.now() - self.start_time).total_seconds(),
            "total_renders": RENDER_COUNTER._value.get(),
            "errors": ERROR_COUNTER._value.get()
        }
```

---

## 10. Quick Reference

### Commands

```bash
# Start headless
blender --background --python engine.py

# Start with API
blender --background --python websocket_server.py -- --port 8765

# Docker
docker-compose up -d

# Kubernetes
kubectl apply -f k8s-deployment.yaml
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ws` | WebSocket | Real-time control |
| `/api/command` | POST | Execute command |
| `/api/viewport` | GET | Get viewport image |
| `/api/render` | POST | Start render |
| `/metrics` | GET | Prometheus metrics |

---

## Tóm Tắt

### Để chạy Blender như Engine cần:

1. **Headless/Headed Mode** - Chạy không cần UI hoặc với off-screen rendering
2. **Python API Server** - WebSocket/HTTP để điều khiển từ xa
3. **Viewport Streaming** - Stream viewport ra web/app khác
4. **Render Pipeline** - Tự động hóa render queue
5. **Security** - Authentication, rate limiting
6. **Monitoring** - Logging, metrics
7. **Deployment** - Docker, Kubernetes cho production

### So sánh với Omnistep:

| Feature | Blender MCP | Omnistep |
|---------|-------------|----------|
| Remote Control | ✅ WebSocket/API | ✅ |
| Viewport Streaming | ✅ Custom implementation | ✅ Built-in |
| Render Pipeline | ✅ Python scripts | ✅ Built-in |
| Docker Support | ✅ Custom Dockerfile | ✅ |
| Cost | Free (Open Source) | Paid |

---

**Tài liệu này cung cấp nền tảng để xây dựng hệ thống tương tự Omnistep với Blender làm engine core.**
