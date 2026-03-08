#!/usr/bin/env python3
"""
Blender Embedded Engine with Viewport Streaming

Run Blender as a service with remote control and viewport streaming.

Usage:
    blender --background --python embedded_engine.py -- --port 8765
"""

import sys
import os

# Add server directory to path
server_dir = os.path.dirname(os.path.abspath(__file__))
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

import asyncio
import json
import base64
import argparse
from typing import Optional, Set
from datetime import datetime

try:
    import bpy
    import gpu
    from gpu_extras.batch import batch_for_shader
except ImportError:
    print("Error: This script must be run inside Blender")
    sys.exit(1)

try:
    from aiohttp import web
except ImportError:
    print("Error: aiohttp not installed. Run: pip install aiohttp")
    sys.exit(1)


# ============================================================================
# Blender Engine Core
# ============================================================================

class BlenderEngine:
    """Blender as embedded engine with off-screen rendering"""

    def __init__(self, width: int = 1280, height: int = 720):
        self.width = width
        self.height = height
        self.offscreen: Optional[gpu.types.GPUOffScreen] = None
        self.setup_offscreen()
        self.start_time = datetime.now()
        self.render_count = 0

    def setup_offscreen(self):
        """Setup off-screen rendering context"""
        try:
            self.offscreen = gpu.types.GPUOffScreen(self.width, self.height)
            print(f"✓ Off-screen buffer created: {self.width}x{self.height}")
        except Exception as e:
            print(f"⚠ Off-screen setup failed: {e}")
            print("  Falling back to simple rendering")
            self.offscreen = None

    def render_viewport(self) -> bytes:
        """Render current viewport to image bytes"""
        if not self.offscreen:
            return self._simple_render()

        try:
            with self.offscreen.bind():
                # Clear buffer
                gpu.state.blend_set('ALPHA')
                gpu.state.depth_test_set('LESS')
                gpu.state.depth_mask_set(True)
                
                # Set viewport
                gpu.state.viewport_set(0, 0, self.width, self.height)
                
                # Update scene
                bpy.context.view_layer.update()
                
                # Render 3D view
                self._render_3d_view()
                
            # Read pixels
            buffer = self.offscreen.color_texture
            pixels = gpu.types.Buffer('BYTE', self.width * self.height * 4, buffer)
            return bytes(pixels)
            
        except Exception as e:
            print(f"Render error: {e}")
            return self._simple_render()

    def _render_3d_view(self):
        """Render 3D viewport"""
        try:
            from gpu_extras.presets import draw_view3d
            
            # Get 3D view settings
            scene = bpy.context.scene
            view_layer = bpy.context.view_layer
            
            # Draw 3D view
            draw_view3d(
                bpy.context,
                view_layer,
                (0, 0, self.width, self.height),
                (0, 0, self.width, self.height)
            )
        except Exception as e:
            # Fallback: simple clear
            gpu.state.clear_color_set((0.1, 0.1, 0.1, 1.0))
            gpu.state.clear_depth_set(1.0)
            gpu.state.clear(gpu.Buffer.COLOR_BIT | gpu.Buffer.DEPTH_BIT)

    def _simple_render(self) -> bytes:
        """Simple fallback render (solid color)"""
        # Create a simple gradient
        pixels = bytearray(self.width * self.height * 4)
        for y in range(self.height):
            for x in range(self.width):
                idx = (y * self.width + x) * 4
                # Gradient background
                r = int(26 + (x / self.width) * 20)
                g = int(26 + (y / self.height) * 20)
                b = int(46)
                pixels[idx:idx+4] = [r, g, b, 255]
        return bytes(pixels)

    def viewport_to_base64(self, pixels: bytes, format: str = 'PNG') -> str:
        """Convert viewport pixels to base64 image"""
        try:
            from PIL import Image
            import io
            
            # Create image (flip vertically for correct orientation)
            img = Image.new('RGBA', (self.width, self.height))
            img.frombytes(pixels)
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
            
            # Encode to base64
            buffer = io.BytesIO()
            img.save(buffer, format=format)
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/{format.lower()};base64,{img_base64}"
            
        except ImportError:
            # PIL not available, return raw base64
            return f"data:image/raw;base64,{base64.b64encode(pixels).decode()}"

    def execute_command(self, command: dict) -> dict:
        """Execute Blender command"""
        method = command.get("method")
        params = command.get("params", {})
        
        commands = {
            "create_object": self.create_object,
            "delete_object": self.delete_object,
            "modify_object": self.modify_object,
            "set_material": self.set_material,
            "get_scene_info": self.get_scene_info,
            "get_object_info": self.get_object_info,
            "render_viewport": self.render_viewport_command,
            "render_final": self.render_final_command,
            "clear_scene": self.clear_scene,
            "set_camera": self.set_camera,
            "set_frame": self.set_frame,
        }
        
        if method in commands:
            try:
                result = commands[method](**params)
                self.render_count += 1
                return {"success": True, **result}
            except Exception as e:
                return {"success": False, "error": str(e)}
        else:
            return {"success": False, "error": f"Unknown method: {method}"}

    def create_object(self, type: str = "cube", location=None, rotation=None, 
                     scale=None, name: str = None, **kwargs) -> dict:
        """Create 3D object"""
        # Deselect all
        bpy.ops.object.select_all(action='DESELECT')
        
        # Create object based on type
        if type == "cube":
            bpy.ops.mesh.primitive_cube_add()
        elif type == "sphere":
            radius = kwargs.get("radius", 1.0)
            bpy.ops.mesh.primitive_uv_sphere_add(radius=radius)
        elif type == "cylinder":
            radius = kwargs.get("radius", 1.0)
            depth = kwargs.get("depth", 2.0)
            bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth)
        elif type == "cone":
            bpy.ops.mesh.primitive_cone_add()
        elif type == "torus":
            bpy.ops.mesh.primitive_torus_add()
        elif type == "plane":
            bpy.ops.mesh.primitive_plane_add()
        elif type == "light":
            light_type = kwargs.get("light_type", "POINT")
            bpy.ops.object.light_add(type=light_type)
        elif type == "camera":
            bpy.ops.object.camera_add()
        else:
            bpy.ops.mesh.primitive_cube_add()
        
        obj = bpy.context.active_object
        
        # Apply transforms
        if location:
            obj.location = location
        if rotation:
            obj.rotation_euler = rotation
        if scale:
            obj.scale = scale
        if name:
            obj.name = name
        
        return {
            "object_name": obj.name,
            "object_type": obj.type,
            "location": list(obj.location)
        }

    def delete_object(self, name: str) -> dict:
        """Delete object"""
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")
        
        bpy.data.objects.remove(obj, do_unlink=True)
        return {"deleted": name}

    def modify_object(self, name: str, location=None, rotation=None, 
                     scale=None) -> dict:
        """Modify object transform"""
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")
        
        if location:
            obj.location = location
        if rotation:
            obj.rotation_euler = rotation
        if scale:
            obj.scale = scale
        
        return {
            "object_name": name,
            "location": list(obj.location),
            "rotation": list(obj.rotation_euler),
            "scale": list(obj.scale)
        }

    def set_material(self, object_name: str, material_name: str,
                    color=None, metallic=None, roughness=None) -> dict:
        """Set material on object"""
        obj = bpy.data.objects.get(object_name)
        if not obj:
            raise ValueError(f"Object not found: {object_name}")
        
        # Get or create material
        mat = bpy.data.materials.get(material_name)
        if not mat:
            mat = bpy.data.materials.new(name=material_name)
            mat.use_nodes = True
        
        # Configure material
        if mat.use_nodes:
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                if color:
                    bsdf.inputs["Base Color"].default_value = (*color[:3], 1.0)
                if metallic is not None:
                    bsdf.inputs["Metallic"].default_value = metallic
                if roughness is not None:
                    bsdf.inputs["Roughness"].default_value = roughness
        
        # Apply to object
        if obj.type == 'MESH':
            if len(obj.material_slots) == 0:
                obj.data.materials.append(mat)
            else:
                obj.material_slots[0].material = mat
        
        return {"material": material_name, "applied_to": object_name}

    def get_scene_info(self) -> dict:
        """Get scene information"""
        scene = bpy.context.scene
        objects = [
            {
                "name": obj.name,
                "type": obj.type,
                "location": list(obj.location),
                "rotation": list(obj.rotation_euler),
                "scale": list(obj.scale)
            }
            for obj in scene.objects
        ]
        
        return {
            "scene_name": scene.name,
            "frame_current": scene.frame_current,
            "frame_start": scene.frame_start,
            "frame_end": scene.frame_end,
            "fps": scene.render.fps,
            "resolution": {
                "x": scene.render.resolution_x,
                "y": scene.render.resolution_y
            },
            "render_engine": scene.render.engine,
            "objects": objects,
            "object_count": len(objects)
        }

    def get_object_info(self, name: str) -> dict:
        """Get object information"""
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")
        
        info = {
            "name": obj.name,
            "type": obj.type,
            "location": list(obj.location),
            "rotation": list(obj.rotation_euler),
            "scale": list(obj.scale),
            "dimensions": list(obj.dimensions)
        }
        
        if obj.type == 'MESH':
            mesh = obj.data
            info["mesh"] = {
                "vertices": len(mesh.vertices),
                "edges": len(mesh.edges),
                "faces": len(mesh.polygons)
            }
        
        return info

    def render_viewport_command(self, format: str = "PNG") -> dict:
        """Render viewport and return as base64"""
        pixels = self.render_viewport()
        img_base64 = self.viewport_to_base64(pixels, format)
        
        return {
            "image": img_base64,
            "width": self.width,
            "height": self.height,
            "format": format,
            "render_count": self.render_count
        }

    def render_final_command(self, filepath: str = None, 
                            resolution_x: int = None,
                            resolution_y: int = None,
                            samples: int = None) -> dict:
        """Final render with Cycles/Eevee"""
        scene = bpy.context.scene
        render = scene.render
        
        # Store original settings
        orig_filepath = render.filepath
        orig_res_x = render.resolution_x
        orig_res_y = render.resolution_y
        
        # Apply new settings
        if filepath:
            render.filepath = filepath
        if resolution_x:
            render.resolution_x = resolution_x
        if resolution_y:
            render.resolution_y = resolution_y
        if samples:
            scene.cycles.samples = samples
        
        # Render
        bpy.ops.render.render(write_still=True)
        
        # Restore settings
        render.filepath = orig_filepath
        render.resolution_x = orig_res_x
        render.resolution_y = orig_res_y
        
        return {
            "success": True,
            "filepath": filepath or render.filepath,
            "resolution": {
                "x": render.resolution_x,
                "y": render.resolution_y
            }
        }

    def clear_scene(self, confirm: bool = False) -> dict:
        """Clear all objects from scene"""
        if not confirm:
            raise ValueError("Must provide confirm=true to clear scene")
        
        count = len(bpy.context.scene.objects)
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        
        return {"cleared_count": count}

    def set_camera(self, location=None, rotation=None, 
                  focal_length: float = None) -> dict:
        """Set active camera"""
        # Create or get camera
        camera = bpy.context.scene.camera
        if not camera:
            bpy.ops.object.camera_add()
            camera = bpy.context.active_object
        
        if location:
            camera.location = location
        if rotation:
            camera.rotation_euler = rotation
        if focal_length:
            camera.data.lens = focal_length
        
        bpy.context.scene.camera = camera
        
        return {
            "camera": camera.name,
            "location": list(camera.location),
            "focal_length": camera.data.lens
        }

    def set_frame(self, frame: int) -> dict:
        """Set current frame"""
        bpy.context.scene.frame_set(frame)
        return {"frame": frame}

    def get_stats(self) -> dict:
        """Get engine statistics"""
        return {
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "render_count": self.render_count,
            "resolution": f"{self.width}x{self.height}",
            "offscreen_enabled": self.offscreen is not None
        }


# ============================================================================
# WebSocket HTTP Server
# ============================================================================

class EngineServer:
    """WebSocket server for Blender Engine"""

    def __init__(self, host: str = 'localhost', port: int = 8765,
                 width: int = 1280, height: int = 720):
        self.host = host
        self.port = port
        self.engine = BlenderEngine(width=width, height=height)
        self.clients: Set = set()
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        """Setup web routes"""
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/ws', self.handle_websocket)
        self.app.router.add_post('/api/command', self.handle_api)
        self.app.router.add_get('/api/viewport', self.handle_viewport)
        self.app.router.add_get('/api/stats', self.handle_stats)
        self.app.router.add_static('/static', 'web_interface', show_index=True)

    async def handle_index(self, request):
        """Serve web interface"""
        return web.Response(text=self._get_html(), content_type='text/html')

    def _get_html(self):
        """Get HTML interface"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎬 Blender Embedded Engine</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            font-family: 'Segoe UI', sans-serif;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        header {
            background: rgba(255,255,255,0.05);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        h1 { color: #e94560; font-size: 1.8em; }
        .status { display: flex; align-items: center; gap: 10px; }
        .status-dot {
            width: 12px; height: 12px;
            border-radius: 50%;
            background: #4ecca3;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 350px;
            gap: 20px;
        }
        .panel {
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 20px;
        }
        .viewport-container {
            background: #000;
            border-radius: 8px;
            overflow: hidden;
            aspect-ratio: 16/9;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        #viewport { max-width: 100%; max-height: 100%; }
        .toolbar {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }
        button {
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            background: #e94560;
            color: white;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }
        button:hover {
            background: #ff6b6b;
            transform: translateY(-2px);
        }
        button.secondary {
            background: #0f3460;
        }
        .object-list {
            max-height: 300px;
            overflow-y: auto;
        }
        .object-item {
            background: rgba(255,255,255,0.05);
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
        }
        .log {
            background: #0d1117;
            border-radius: 8px;
            padding: 15px;
            height: 200px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 12px;
        }
        .log-entry { margin: 3px 0; }
        .log-entry.info { color: #4ecca3; }
        .log-entry.error { color: #ff6b6b; }
        .stats { margin-top: 15px; }
        .stat-item {
            display: flex;
            justify-content: space-between;
            padding: 8px;
            background: rgba(255,255,255,0.05);
            border-radius: 4px;
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎬 Blender Embedded Engine</h1>
            <div class="status">
                <div class="status-dot"></div>
                <span id="statusText">Connected</span>
            </div>
        </header>

        <div class="main-grid">
            <div class="panel">
                <h2>🖼️ Viewport</h2>
                <div class="viewport-container">
                    <img id="viewport" alt="Viewport" />
                </div>
                <div class="toolbar">
                    <button onclick="createObject('cube')">📦 Cube</button>
                    <button onclick="createObject('sphere')">🔮 Sphere</button>
                    <button onclick="createObject('cylinder')">🛢️ Cylinder</button>
                    <button onclick="createObject('cone')">🔺 Cone</button>
                    <button onclick="createObject('torus')">🍩 Torus</button>
                    <button onclick="createObject('plane')">📄 Plane</button>
                    <button onclick="createObject('light')">💡 Light</button>
                    <button onclick="createObject('camera')">📷 Camera</button>
                    <button class="secondary" onclick="refreshViewport()">🔄 Refresh</button>
                    <button class="secondary" onclick="clearScene()">🗑️ Clear</button>
                </div>
            </div>

            <div class="panel">
                <h2>📊 Scene Objects</h2>
                <div class="object-list" id="objectList">
                    <div style="color: #888;">Loading...</div>
                </div>

                <div class="stats">
                    <h3>📈 Statistics</h3>
                    <div class="stat-item">
                        <span>Renders:</span>
                        <span id="statRenders">0</span>
                    </div>
                    <div class="stat-item">
                        <span>Resolution:</span>
                        <span id="statResolution">1280x720</span>
                    </div>
                    <div class="stat-item">
                        <span>Objects:</span>
                        <span id="statObjects">0</span>
                    </div>
                </div>

                <h3 style="margin-top: 20px;">📜 Activity Log</h3>
                <div class="log" id="log"></div>
            </div>
        </div>
    </div>

    <script>
        let ws;
        let renderCount = 0;

        function connect() {
            ws = new WebSocket('ws://' + window.location.host + '/ws');
            
            ws.onopen = () => {
                log('Connected to Blender Engine', 'info');
                refreshScene();
            };
            
            ws.onclose = () => {
                log('Disconnected - Reconnecting...', 'error');
                setTimeout(connect, 2000);
            };
            
            ws.onmessage = (e) => {
                const data = JSON.parse(e.data);
                handleMessage(data);
            };
        }

        function handleMessage(data) {
            if (data.type === 'viewport') {
                document.getElementById('viewport').src = data.image;
                document.getElementById('statRenders').textContent = data.render_count;
            } else if (data.type === 'scene') {
                updateObjectList(data.objects);
                document.getElementById('statObjects').textContent = data.object_count;
            } else if (data.success !== undefined) {
                log('Command executed: ' + (data.object_name || data.method || 'OK'), 'info');
                refreshViewport();
            } else if (data.error) {
                log('Error: ' + data.error, 'error');
            }
        }

        function sendCommand(method, params = {}) {
            ws.send(JSON.stringify({
                method: method,
                params: params
            }));
        }

        function createObject(type) {
            sendCommand('create_object', { type: type });
            log('Creating ' + type, 'info');
        }

        function refreshViewport() {
            sendCommand('render_viewport');
        }

        function refreshScene() {
            sendCommand('get_scene_info');
            refreshViewport();
        }

        function clearScene() {
            if (confirm('Clear all objects?')) {
                sendCommand('clear_scene', { confirm: true });
            }
        }

        function updateObjectList(objects) {
            const list = document.getElementById('objectList');
            if (!objects || objects.length === 0) {
                list.innerHTML = '<div style="color: #888;">No objects</div>';
                return;
            }
            list.innerHTML = objects.map(obj => `
                <div class="object-item">
                    <span>${obj.name} (${obj.type})</span>
                    <span style="color: #888;">${obj.location[0].toFixed(1)}, ${obj.location[1].toFixed(1)}, ${obj.location[2].toFixed(1)}</span>
                </div>
            `).join('');
        }

        function log(message, type = 'info') {
            const logDiv = document.getElementById('log');
            const time = new Date().toLocaleTimeString();
            logDiv.innerHTML += `<div class="log-entry ${type}">[${time}] ${message}</div>`;
            logDiv.scrollTop = logDiv.scrollHeight;
        }

        // Auto-refresh viewport every 2 seconds
        setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                refreshViewport();
            }
        }, 2000);

        // Start
        connect();
        log('Blender Embedded Engine initialized', 'info');
    </script>
</body>
</html>
        """

    async def handle_websocket(self, request):
        """WebSocket handler"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.clients.add(ws)
        print(f"[+] Client connected. Total: {len(self.clients)}")

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    command = json.loads(msg.data)
                    result = self.engine.execute_command(command)
                    
                    # Add viewport for render commands
                    if command.get("method") == "render_viewport":
                        result["type"] = "viewport"
                    
                    await ws.send_json(result)
                    
                elif msg.type == web.WSMsgType.ERROR:
                    print(f"WebSocket error: {ws.exception()}")
        finally:
            self.clients.remove(ws)
            print(f"[-] Client disconnected. Total: {len(self.clients)}")

        return ws

    async def handle_api(self, request):
        """REST API handler"""
        try:
            command = await request.json()
            result = self.engine.execute_command(command)
            return web.json_response(result)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    async def handle_viewport(self, request):
        """Viewport endpoint"""
        result = self.engine.render_viewport_command()
        return web.json_response(result)

    async def handle_stats(self, request):
        """Statistics endpoint"""
        stats = self.engine.get_stats()
        return web.json_response(stats)

    def run(self):
        """Start server"""
        print("=" * 60)
        print("🎬 Blender Embedded Engine")
        print("=" * 60)
        print(f"📍 Web Interface: http://{self.host}:{self.port}")
        print(f"🔌 WebSocket: ws://{self.host}:{self.port}/ws")
        print(f"📊 API: http://{self.host}:{self.port}/api/command")
        print(f"🖼️ Viewport: {self.engine.width}x{self.engine.height}")
        print(f"⏱️  Off-screen: {'Enabled' if self.engine.offscreen else 'Disabled'}")
        print("=" * 60)
        print("Press Ctrl+C to stop")
        print("=" * 60)
        
        web.run_app(self.app, host=self.host, port=self.port)


# ============================================================================
# Main Entry Point
# ============================================================================

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Blender Embedded Engine")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on")
    parser.add_argument("--width", type=int, default=1280, help="Viewport width")
    parser.add_argument("--height", type=int, default=720, help="Viewport height")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    # Create and start server
    server = EngineServer(
        host=args.host,
        port=args.port,
        width=args.width,
        height=args.height
    )
    server.run()
