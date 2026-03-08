# Đánh giá Tích hợp MCP và Bot cho Blender

**Ngày đánh giá:** March 2026  
**Mục đích:** Tự động hóa quy trình làm việc Blender thông qua Model Context Protocol (MCP) và bot

---

## Tóm tắt Executive

| Khía cạnh | Đánh giá | Ghi chú |
|-----------|----------|---------|
| **Khả thi kỹ thuật** | ✅ **CAO** | Python API mạnh mẽ, kiến trúc mở |
| **Mức độ ưu tiên** | 🔴 **CAO** | Xu hướng AI/LLM integration đang phát triển |
| **Độ phức tạp** | 🟡 **TRUNG BÌNH** | Cần lớp abstraction cho MCP |
| **Rủi ro** | 🟢 **THẤP** | Không ảnh hưởng core, chạy như addon |
| **ROI tiềm năng** | ✅ **CAO** | Tự động hóa workflow, AI-assisted modeling |

---

## 1. Tổng quan về MCP (Model Context Protocol)

### 1.1 MCP là gì?

Model Context Protocol là giao thức chuẩn cho phép:
- Kết nối LLM với external tools và data sources
- Thực thi commands thông qua function calling
- Truy cập context từ nhiều nguồn khác nhau

### 1.2 MCP Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   LLM/AI    │────▶│  MCP Server  │────▶│   Blender   │
│   Client    │◀────│   (Python)   │◀────│   Python    │
└─────────────┘     └──────────────┘     └─────────────┘
```

---

## 2. Phân tích Khả năng Tích hợp

### 2.1 Điểm mạnh của Blender cho Integration

#### ✅ Python API Toàn diện

```python
# Truy cập toàn bộ Blender data
import bpy

# Context access
obj = bpy.context.object
scene = bpy.context.scene

# Operator execution
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.primitive_box_add()

# Data manipulation
mesh = obj.data
mesh.vertices[0].co = (1.0, 2.0, 3.0)

# Event handlers
@bpy.app.handlers.persistent
def on_save_post(handler, context):
    print("File saved!")
```

#### ✅ Event System Mạnh mẽ

| Handler | Mục đích |
|---------|----------|
| `bpy.app.handlers.load_post` | Sau khi load file |
| `bpy.app.handlers.save_pre` | Trước khi save file |
| `bpy.app.handlers.frame_change_pre` | Trước mỗi frame |
| `bpy.app.handlers.render_init` | Khi bắt đầu render |
| `bpy.app.handlers.depsgraph_update` | Khi depsgraph update |

#### ✅ Background Mode

```bash
# Chạy Blender không GUI
blender --background --python script.py

# Execute command
blender --background file.blend --python-expr "bpy.ops.object.mode_set(mode='EDIT')"
```

#### ✅ Timer System

```python
import bpy

@bpy.app.timers.register
def periodic_task():
    # Chạy mỗi 1 giây
    do_something()
    return 1.0
```

### 2.2 Hạn chế và Thách thức

#### ⚠️ Không có Native Network Support

Blender không có built-in HTTP/WebSocket server:

```python
# ❌ Không có API này
bpy.network.start_server()  # Không tồn tại

# ✅ Phải tự implement
import socket
import threading
```

#### ⚠️ Thread Safety

```python
# ⚠️ Blender không thread-safe cho hầu hết API
# Chỉ main thread được gọi bpy.* APIs

# Giải pháp: Queue-based communication
import bpy
import threading
import queue

command_queue = queue.Queue()

def worker():
    while True:
        cmd = command_queue.get()
        # Execute in main thread via timer
```

#### ⚠️ Blocking Operations

```python
# ⚠️ Một số operations blocking
bpy.ops.render.render()  # Block cho đến khi xong

# ✅ Giải pháp: Background threads cho render
bpy.context.scene.render.use_file_extension = True
```

---

## 3. Kiến trúc Đề xuất

### 3.1 MCP Server Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Client (LLM)                      │
│                    (Claude, GPT-4, etc.)                 │
└─────────────────────────────────────────────────────────┘
                            │
                            │ MCP Protocol (JSON-RPC)
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  MCP Server for Blender                  │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Transport Layer (WebSocket/HTTP/stdio)            │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Command Router & Validator                        │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Blender API Wrapper                               │ │
│  │  - Object Operations                               │ │
│  │  - Mesh Operations                                 │ │
│  │  - Material Operations                             │ │
│  │  - Animation Operations                            │ │
│  │  - Render Operations                               │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Context Provider                                  │ │
│  │  - Scene state                                     │ │
│  │  - Selected objects                                │ │
│  │  - Current mode                                    │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                            │
                            │ Python API
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    Blender Application                   │
│                    (bpy.* APIs)                          │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Triển khai MCP Server

#### Option 1: Standalone MCP Server (Recommended)

```python
# mcp_blender_server.py
import bpy
import json
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server

server = Server("blender")

@server.list_tools()
async def list_tools():
    return [
        {
            "name": "create_object",
            "description": "Create a 3D object",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["cube", "sphere", "cylinder"]},
                    "location": {"type": "array", "items": {"type": "number"}},
                },
                "required": ["type"],
            },
        },
        {
            "name": "get_scene_info",
            "description": "Get current scene information",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "modify_mesh",
            "description": "Modify mesh vertices",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "object_name": {"type": "string"},
                    "vertex_index": {"type": "integer"},
                    "location": {"type": "array", "items": {"type": "number"}},
                },
                "required": ["object_name", "vertex_index", "location"],
            },
        },
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "create_object":
        obj_type = arguments["type"]
        location = arguments.get("location", (0, 0, 0))
        
        if obj_type == "cube":
            bpy.ops.mesh.primitive_cube_add(location=location)
        elif obj_type == "sphere":
            bpy.ops.mesh.primitive_uv_sphere_add(location=location)
        elif obj_type == "cylinder":
            bpy.ops.mesh.primitive_cylinder_add(location=location)
        
        return {"success": True, "object": bpy.context.object.name}
    
    elif name == "get_scene_info":
        objects = [
            {
                "name": obj.name,
                "type": obj.type,
                "location": list(obj.location),
                "selected": obj.select_get(),
            }
            for obj in bpy.context.scene.objects
        ]
        return {
            "scene": bpy.context.scene.name,
            "frame": bpy.context.scene.frame_current,
            "objects": objects,
        }
    
    elif name == "modify_mesh":
        obj = bpy.data.objects.get(arguments["object_name"])
        if not obj:
            return {"success": False, "error": "Object not found"}
        
        mesh = obj.data
        vertex = mesh.vertices[arguments["vertex_index"]]
        vertex.co = arguments["location"]
        
        return {"success": True, "vertex": arguments["vertex_index"]}
    
    return {"success": False, "error": "Unknown tool"}

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )

if __name__ == "__main__":
    asyncio.run(main())
```

#### Option 2: WebSocket-based Server

```python
# websocket_blender_server.py
import bpy
import json
import asyncio
import websockets

class BlenderWebSocketServer:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.clients = set()
    
    async def handler(self, websocket):
        self.clients.add(websocket)
        try:
            async for message in websocket:
                response = await self.process_message(json.loads(message))
                await websocket.send(json.dumps(response))
        finally:
            self.clients.remove(websocket)
    
    async def process_message(self, message):
        """Process JSON-RPC like messages"""
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")
        
        try:
            result = await self.execute_command(method, params)
            return {
                "id": msg_id,
                "result": result,
                "error": None,
            }
        except Exception as e:
            return {
                "id": msg_id,
                "result": None,
                "error": str(e),
            }
    
    async def execute_command(self, method, params):
        """Execute Blender commands"""
        commands = {
            "create_object": self.create_object,
            "delete_object": self.delete_object,
            "get_scene_info": self.get_scene_info,
            "set_material": self.set_material,
            "animate_object": self.animate_object,
            "render_scene": self.render_scene,
        }
        
        if method not in commands:
            raise ValueError(f"Unknown method: {method}")
        
        return await commands[method](params)
    
    async def create_object(self, params):
        obj_type = params.get("type", "cube")
        location = params.get("location", (0, 0, 0))
        
        ops_map = {
            "cube": bpy.ops.mesh.primitive_cube_add,
            "sphere": bpy.ops.mesh.primitive_uv_sphere_add,
            "cylinder": bpy.ops.mesh.primitive_cylinder_add,
            "plane": bpy.ops.mesh.primitive_plane_add,
        }
        
        if obj_type not in ops_map:
            raise ValueError(f"Unknown object type: {obj_type}")
        
        ops_map[obj_type](location=location)
        obj = bpy.context.object
        
        return {
            "success": True,
            "object_name": obj.name,
            "object_type": obj.type,
        }
    
    async def delete_object(self, params):
        obj_name = params.get("name")
        obj = bpy.data.objects.get(obj_name)
        
        if not obj:
            raise ValueError(f"Object not found: {obj_name}")
        
        bpy.data.objects.remove(obj, do_unlink=True)
        return {"success": True}
    
    async def get_scene_info(self, params):
        objects = []
        for obj in bpy.context.scene.objects:
            objects.append({
                "name": obj.name,
                "type": obj.type,
                "location": list(obj.location),
                "rotation": list(obj.rotation_euler),
                "scale": list(obj.scale),
                "selected": obj.select_get(),
                "hidden": obj.hide_get(),
            })
        
        return {
            "scene": bpy.context.scene.name,
            "frame": bpy.context.scene.frame_current,
            "frame_start": bpy.context.scene.frame_start,
            "frame_end": bpy.context.scene.frame_end,
            "objects": objects,
            "object_count": len(objects),
        }
    
    async def set_material(self, params):
        obj_name = params.get("object_name")
        material_name = params.get("material_name")
        color = params.get("color")
        
        obj = bpy.data.objects.get(obj_name)
        if not obj:
            raise ValueError(f"Object not found: {obj_name}")
        
        mat = bpy.data.materials.get(material_name)
        if not mat:
            mat = bpy.data.materials.new(name=material_name)
            mat.use_nodes = True
        
        if color:
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        
        if len(obj.material_slots) == 0:
            obj.data.materials.append(mat)
        else:
            obj.material_slots[0].material = mat
        
        return {"success": True, "material": mat.name}
    
    async def render_scene(self, params):
        output_path = params.get("filepath", "//render.png")
        
        bpy.context.scene.render.filepath = output_path
        bpy.ops.render.render(write_still=True)
        
        return {"success": True, "filepath": output_path}
    
    def start(self):
        start_server = websockets.serve(self.handler, self.host, self.port)
        asyncio.get_event_loop().run_until_complete(start_server)
        print(f"Blender MCP Server started on ws://{self.host}:{self.port}")
        asyncio.get_event_loop().run_forever()

# Register timer to process commands
server = None

@bpy.app.timers.register
def process_websocket():
    # Process any pending websocket messages
    return 0.1  # Run every 100ms

if __name__ == "__main__":
    server = BlenderWebSocketServer()
    server.start()
```

### 3.3 Blender Addon Implementation

```python
# mcp_blender_addon.py
bl_info = {
    "name": "MCP Blender Server",
    "author": "Your Name",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > MCP",
    "description": "Enable MCP server for AI automation",
    "category": "Interface",
}

import bpy
import threading
import json
from bpy.props import IntProperty, BoolProperty, StringProperty
from bpy.types import Panel, Operator, PropertyGroup

class MCPServerProperties(PropertyGroup):
    port: IntProperty(
        name="Port",
        default=8765,
        min=1024,
        max=65535,
    )
    is_running: BoolProperty(
        name="Running",
        default=False,
    )
    host: StringProperty(
        name="Host",
        default="localhost",
    )

class MCPStartServer(Operator):
    bl_idname = "mcp.start_server"
    bl_label = "Start MCP Server"
    
    def execute(self, context):
        props = context.scene.mcp_server
        
        # Start server in background thread
        from . import mcp_server
        server = mcp_server.BlenderWebSocketServer(
            host=props.host,
            port=props.port,
        )
        
        thread = threading.Thread(target=server.start, daemon=True)
        thread.start()
        
        props.is_running = True
        self.report({'INFO'}, f"MCP Server started on {props.host}:{props.port}")
        return {'FINISHED'}

class MCPStopServer(Operator):
    bl_idname = "mcp.stop_server"
    bl_label = "Stop MCP Server"
    
    def execute(self, context):
        props = context.scene.mcp_server
        props.is_running = False
        self.report({'INFO'}, "MCP Server stopped")
        return {'FINISHED'}

class MCPPanel(Panel):
    bl_label = "MCP Server"
    bl_idname = "VIEW3D_PT_mcp_server"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MCP"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.mcp_server
        
        layout.prop(props, "host")
        layout.prop(props, "port")
        
        row = layout.row()
        if props.is_running:
            row.operator("mcp.stop_server", text="Stop Server", icon='PAUSE')
        else:
            row.operator("mcp.start_server", text="Start Server", icon='PLAY')
        
        layout.separator()
        layout.label(text="Available Tools:")
        tools = [
            "create_object",
            "delete_object",
            "get_scene_info",
            "set_material",
            "animate_object",
            "render_scene",
        ]
        for tool in tools:
            layout.label(text=f"  • {tool}", icon='DOT')

classes = (
    MCPServerProperties,
    MCPStartServer,
    MCPStopServer,
    MCPPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.mcp_server = bpy.props.PointerProperty(type=MCPServerProperties)

def unregister():
    del bpy.types.Scene.mcp_server
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
```

---

## 4. Use Cases và Automation Scenarios

### 4.1 AI-Assisted Modeling

```python
# User prompt: "Create a cityscape with 10 buildings"
# LLM generates MCP calls:

[
    {"method": "create_object", "params": {"type": "cube", "location": [0, 0, 0]}},
    {"method": "modify_mesh", "params": {"object_name": "Cube", "scale": [2, 2, 10]}},
    {"method": "create_object", "params": {"type": "cube", "location": [5, 0, 0]}},
    {"method": "modify_mesh", "params": {"object_name": "Cube.001", "scale": [3, 3, 15]}},
    # ... more buildings
]
```

### 4.2 Automated Rigging

```python
# User prompt: "Rig this character for animation"
# Bot executes:

[
    {"method": "create_armature", "params": {"name": "CharacterRig"}},
    {"method": "create_bone", "params": {"name": "spine", "head": [0, 0, 0], "tail": [0, 0, 1]}},
    {"method": "create_bone", "params": {"name": "head", "parent": "spine"}},
    {"method": "create_bone", "params": {"name": "arm_L", "parent": "spine"}},
    {"method": "create_bone", "params": {"name": "arm_R", "parent": "spine"}},
    {"method": "auto_weight_paint", "params": {"object": "Character"}},
]
```

### 4.3 Batch Processing

```python
# User prompt: "Export all objects as separate FBX files"
# Bot executes:

import bpy

for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        # Select only this object
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        # Export
        bpy.ops.export_scene.fbx(
            filepath=f"//exports/{obj.name}.fbx",
            use_selection=True,
        )
```

### 4.4 Procedural Generation

```python
# User prompt: "Generate a forest with random trees"
# Bot executes:

import random

for i in range(100):
    x = random.uniform(-50, 50)
    y = random.uniform(-50, 50)
    
    # Create tree trunk
    bpy.ops.mesh.primitive_cylinder_add(
        radius=random.uniform(0.2, 0.5),
        depth=random.uniform(5, 10),
        location=(x, y, random.uniform(2, 5)),
    )
    
    # Create tree crown
    bpy.ops.mesh.primitive_ico_sphere_add(
        radius=random.uniform(2, 4),
        location=(x, y, random.uniform(8, 12)),
    )
```

### 4.5 Animation Automation

```python
# User prompt: "Animate the ball bouncing from frame 1 to 60"
# Bot executes:

import bpy

ball = bpy.data.objects.get("Ball")
ball.location = (-10, 0, 5)
ball.keyframe_insert(data_path="location", frame=1)

ball.location = (0, 0, 0)
ball.keyframe_insert(data_path="location", frame=30)

ball.location = (10, 0, 5)
ball.keyframe_insert(data_path="location", frame=60)

# Add physics modifier
mod = ball.modifiers.new(name="Bounce", type='SOFT_BODY')
```

---

## 5. Available MCP Tools Definition

### 5.1 Core Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `create_object` | Create 3D primitive | `type`, `location`, `rotation`, `scale` |
| `delete_object` | Delete an object | `object_name` |
| `get_scene_info` | Get scene state | - |
| `get_object_info` | Get object details | `object_name` |
| `modify_object` | Transform object | `object_name`, `location`, `rotation`, `scale` |
| `set_material` | Apply/create material | `object_name`, `material_name`, `color` |
| `modify_mesh` | Edit mesh data | `object_name`, `vertex_index`, `location` |

### 5.2 Advanced Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `create_armature` | Create skeleton | `name`, `bones` |
| `create_animation` | Keyframe animation | `object_name`, `frames`, `locations` |
| `render_scene` | Render current scene | `filepath`, `resolution`, `samples` |
| `export_file` | Export to format | `filepath`, `format`, `options` |
| `import_file` | Import file | `filepath`, `format` |
| `apply_modifier` | Add modifier | `object_name`, `modifier_type`, `options` |
| `create_light` | Add light | `type`, `location`, `energy`, `color` |
| `create_camera` | Add camera | `location`, `focal_length` |

### 5.3 Context Tools

| Tool | Description | Returns |
|------|-------------|---------|
| `get_selected_objects` | Get current selection | List of object names |
| `get_active_object` | Get active object | Object name |
| `get_current_mode` | Get edit mode | Mode string |
| `get_scene_stats` | Scene statistics | Object count, vertex count, etc. |
| `get_render_settings` | Current render settings | Resolution, samples, engine |

---

## 6. Lộ trình Triển khai

### Phase 1: Foundation (2-4 weeks)

- [ ] Tạo MCP Server basic implementation
- [ ] Implement core tools (create, delete, modify)
- [ ] Tạo Blender addon cho UI control
- [ ] Viết documentation và examples

### Phase 2: Advanced Features (4-6 weeks)

- [ ] Add advanced tools (rigging, animation)
- [ ] Implement context providers
- [ ] Add WebSocket transport layer
- [ ] Create Python SDK for clients

### Phase 3: Integration (4-8 weeks)

- [ ] Integrate with popular LLMs (Claude, GPT-4)
- [ ] Create pre-built automation templates
- [ ] Add support for multi-user scenarios
- [ ] Implement security and access control

### Phase 4: Production (Ongoing)

- [ ] Performance optimization
- [ ] Error handling and recovery
- [ ] Monitoring and logging
- [ ] Community contributions

---

## 7. Security Considerations

### 7.1 Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Unauthorized Access** | HIGH | Authentication, API keys |
| **Destructive Commands** | HIGH | Confirmation prompts, undo support |
| **Resource Exhaustion** | MEDIUM | Rate limiting, timeouts |
| **Data Leakage** | MEDIUM | Access control, encryption |

### 7.2 Security Implementation

```python
class SecureMCPServer(BlenderWebSocketServer):
    def __init__(self, *args, api_key=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = api_key
        self.allowed_commands = set()
        self.rate_limiter = RateLimiter(max_requests=100, window=60)
    
    async def handler(self, websocket):
        # Authenticate
        headers = websocket.request_headers
        if headers.get("X-API-Key") != self.api_key:
            await websocket.close(1008, "Unauthorized")
            return
        
        # Rate limiting
        if not self.rate_limiter.allow():
            await websocket.close(1008, "Rate limit exceeded")
            return
        
        await super().handler(websocket)
    
    async def execute_command(self, method, params):
        # Command whitelist
        if method not in self.allowed_commands:
            raise ValueError(f"Command not allowed: {method}")
        
        # Destructive command confirmation
        if method in ["delete_object", "clear_scene"]:
            if not params.get("confirm"):
                raise ValueError("Confirmation required for destructive command")
        
        return await super().execute_command(method, params)
```

---

## 8. So sánh với Giải pháp Khác

| Giải pháp | Ưu điểm | Nhược điểm | Phù hợp cho |
|-----------|---------|------------|-------------|
| **MCP Server** | Chuẩn hóa, LLM-native | Cần setup thêm | AI automation |
| **Python Scripts** | Đơn giản, native | Không interactive | Batch processing |
| **Command Line** | Không cần GUI | Hạn chế tính năng | Render farms |
| **HTTP API** | Web-accessible | Cần self-host | Remote control |
| **WebSocket** | Real-time, bidirectional | Complex hơn | Interactive bots |

---

## 9. Kết luận và Khuyến nghị

### 9.1 Thời điểm Hiện tại: ✅ THUẬN LỢI

**Lý do:**

1. **Blender 4.x ổn định** - API mature, Python 3.11+
2. **MCP ecosystem đang phát triển** - Nhiều LLM hỗ trợ
3. **Nhu cầu automation cao** - Studio, indie artists cần
4. **Cộng đồng lớn** - Dễ nhận contribution

### 9.2 Khuyến nghị

#### Ưu tiên Cao (Start Now)

1. **Phát triển MCP Server cơ bản**
   - Focus vào core operations
   - WebSocket transport
   - Basic security

2. **Tạo addon Blender**
   - UI cho start/stop server
   - Log viewer
   - Connection status

3. **Documentation**
   - API reference
   - Use case examples
   - Integration guides

#### Ưu tiên Trung bình (Phase 2)

1. **Advanced tools**
   - Rigging automation
   - Animation tools
   - Batch processing

2. **LLM Integration**
   - Claude integration
   - GPT-4 integration
   - **Ollama localhost integration** ⭐
   - Custom prompts library

#### Ưu tiên Thấp (Future)

1. **Multi-user support**
2. **Cloud deployment**
3. **Marketplace for automation scripts**

### 9.3 Tài nguyên Cần thiết

| Resource | Số lượng | Ghi chú |
|----------|----------|---------|
| **Developers** | 2-3 | Python, Blender API, MCP |
| **Time** | 3-6 months | Đến MVP |
| **Testers** | 5-10 | Community beta |
| **Infrastructure** | Minimal | GitHub, documentation site |

---

## 10. Ollama Local LLM Integration

### 10.1 Tại sao Ollama?

| Ưu điểm | Mô tả |
|---------|-------|
| **🔒 Privacy** | Chạy local, không gửi data ra ngoài |
| **💰 Free** | Không cần API key, không tốn phí |
| **⚡ Fast** | Không network latency |
| **🎯 Customizable** | Fine-tune với workflow riêng |
| **📦 Offline** | Làm việc không cần internet |

### 10.2 Cài đặt Ollama

**macOS:**
```bash
# Install
brew install ollama

# Start server
ollama serve

# Pull model
ollama pull llama2
ollama pull codellama
ollama pull mistral
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
ollama pull llama2
```

**Windows:**
```powershell
# Download từ https://ollama.com/download
ollama pull llama2
```

### 10.3 Cấu hình Ollama cho Blender MCP

**File: `ollama_blender_config.py`**

```python
#!/usr/bin/env python3
"""
Ollama Integration for Blender MCP Server.

Run local LLM on localhost:11434 for Blender automation.
"""

import requests
import json
from typing import List, Dict, Optional, Generator


class OllamaClient:
    """Client for Ollama local LLM."""

    def __init__(self, host: str = "http://localhost:11434", model: str = "llama2"):
        self.host = host
        self.model = model
        self.base_url = f"{host}/api"

    def chat(self, messages: List[Dict], tools: Optional[List[Dict]] = None) -> Dict:
        """
        Send chat request to Ollama.

        Args:
            messages: List of {role, content} dicts
            tools: Optional tool definitions

        Returns:
            Response dict with content
        """
        url = f"{self.base_url}/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        # Add system prompt for Blender assistant
        if not any(m["role"] == "system" for m in messages):
            system_prompt = """You are a Blender 3D automation assistant. 
You help users create 3D content by translating natural language into Blender operations.

When user asks to create something:
1. Understand what they want
2. Break it into specific Blender operations
3. Return JSON with tool calls

Available tools: create_object, delete_object, modify_object, set_material, 
create_camera, create_light, render_scene, export_file

Always respond with valid JSON including tool calls when appropriate."""

            messages.insert(0, {"role": "system", "content": system_prompt})

        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()

        return response.json()

    def chat_stream(self, messages: List[Dict]) -> Generator[str, None, None]:
        """Stream response from Ollama."""
        url = f"{self.base_url}/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }

        response = requests.post(url, json=payload, stream=True, timeout=60)

        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                if "message" in data and "content" in data["message"]:
                    yield data["message"]["content"]

    def generate(self, prompt: str) -> str:
        """Generate completion for a prompt."""
        url = f"{self.base_url}/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()

        return response.json().get("response", "")

    def list_models(self) -> List[str]:
        """List available models."""
        url = f"{self.base_url}/tags"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        return [m["name"] for m in response.json().get("models", [])]

    def is_available(self) -> bool:
        """Check if Ollama server is running."""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


class OllamaBlenderAssistant:
    """Blender assistant using Ollama local LLM."""

    def __init__(self, host: str = "http://localhost:11434", model: str = "codellama"):
        self.client = OllamaClient(host=host, model=model)
        self.conversation_history: List[Dict] = []
        self.available_tools = self._get_tool_definitions()

    def _get_tool_definitions(self) -> List[Dict]:
        """Get tool definitions for LLM."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_object",
                    "description": "Create a 3D primitive object",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["cube", "sphere", "cylinder", "cone", "torus", "plane"]
                            },
                            "location": {"type": "array", "items": {"type": "number"}},
                            "name": {"type": "string"}
                        },
                        "required": ["type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "modify_object",
                    "description": "Modify object transform",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "location": {"type": "array", "items": {"type": "number"}},
                            "rotation": {"type": "array", "items": {"type": "number"}},
                            "scale": {"type": "array", "items": {"type": "number"}}
                        },
                        "required": ["name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_scene_info",
                    "description": "Get current scene information"
                }
            }
        ]

    def execute(self, user_message: str, execute_tools: bool = True) -> Dict:
        """
        Execute user request.

        Args:
            user_message: Natural language request
            execute_tools: Whether to execute tool calls

        Returns:
            Response dict with content and tool calls
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Get response from Ollama
        response = self.client.chat(
            messages=self.conversation_history,
            tools=self.available_tools
        )

        assistant_message = response.get("message", {}).get("content", "")

        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        # Parse tool calls from response
        tool_calls = self._parse_tool_calls(assistant_message)

        # Execute tools if enabled
        tool_results = []
        if execute_tools and tool_calls:
            for tool_call in tool_calls:
                result = self._execute_tool(tool_call)
                tool_results.append(result)

                # Add tool result to conversation
                self.conversation_history.append({
                    "role": "system",
                    "content": f"Tool result: {json.dumps(result)}"
                })

        return {
            "content": assistant_message,
            "tool_calls": tool_calls,
            "tool_results": tool_results,
            "model": self.client.model
        }

    def _parse_tool_calls(self, response: str) -> List[Dict]:
        """Parse tool calls from LLM response."""
        tool_calls = []

        # Look for JSON in response
        try:
            # Try to find JSON object
            start = response.find('{')
            end = response.rfind('}') + 1

            if start >= 0 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)

                # Check for tool_call format
                if "tool_call" in data:
                    tool_calls.append(data["tool_call"])
                elif "tool_calls" in data:
                    tool_calls.extend(data["tool_calls"])
        except json.JSONDecodeError:
            pass

        return tool_calls

    def _execute_tool(self, tool_call: Dict) -> Dict:
        """Execute a tool call (placeholder - integrate with Blender tools)."""
        tool_name = tool_call.get("name")
        params = tool_call.get("parameters", tool_call.get("arguments", {}))

        # This would integrate with actual Blender tools
        # For now, return simulated response
        return {
            "tool": tool_name,
            "status": "executed",
            "parameters": params
        }

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

    def get_history(self) -> List[Dict]:
        """Get conversation history."""
        return self.conversation_history.copy()


def check_ollama_status(host: str = "http://localhost:11434") -> Dict:
    """Check Ollama server status and available models."""
    client = OllamaClient(host=host)

    if not client.is_available():
        return {
            "status": "offline",
            "message": "Ollama server not running. Start with: ollama serve"
        }

    models = client.list_models()

    return {
        "status": "online",
        "host": host,
        "models": models,
        "recommended": "codellama" if "codellama" in models else "llama2"
    }


# CLI usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "status":
        status = check_ollama_status()
        print(json.dumps(status, indent=2))
    else:
        # Interactive mode
        print("Ollama Blender Assistant")
        print("=" * 40)
        print("Models available:", check_ollama_status()["models"])
        print("Type 'quit' to exit\n")

        assistant = OllamaBlenderAssistant(model="codellama")

        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ("quit", "exit"):
                break

            response = assistant.execute(user_input)
            print(f"Assistant: {response['content']}")

            if response["tool_calls"]:
                print(f"Tool calls: {response['tool_calls']}")
```

### 10.4 Tích hợp vào Blender MCP Server

**File: `server/ollama_integration.py`**

```python
#!/usr/bin/env python3
"""
Ollama integration for Blender MCP WebSocket Server.

Add this to websocket_server.py to enable local LLM control.
"""

from ollama_blender_config import OllamaBlenderAssistant, check_ollama_status
from tools import BlenderTools


class OllamaEnabledServer:
    """WebSocket server with Ollama LLM integration."""

    def __init__(self, ollama_host: str = "http://localhost:11434", 
                 model: str = "codellama"):
        self.blender_tools = BlenderTools()
        self.ollama_assistant = OllamaBlenderAssistant(
            host=ollama_host, 
            model=model
        )
        self.ollama_available = check_ollama_status(ollama_host)["status"] == "online"

    async def handle_chat_request(self, websocket, message: str) -> dict:
        """Handle natural language chat with Ollama."""
        if not self.ollama_available:
            return {
                "success": False,
                "error": "Ollama server not available. Start with: ollama serve"
            }

        # Process with Ollama
        response = self.ollama_assistant.execute(message, execute_tools=True)

        # Execute actual Blender tools
        for tool_call in response.get("tool_calls", []):
            tool_name = tool_call.get("name")
            params = tool_call.get("parameters", {})

            if hasattr(self.blender_tools, tool_name):
                try:
                    result = getattr(self.blender_tools, tool_name)(**params)
                    response["tool_results"].append({
                        "tool": tool_name,
                        "result": result
                    })
                except Exception as e:
                    response["tool_results"].append({
                        "tool": tool_name,
                        "error": str(e)
                    })

        return {
            "success": True,
            "response": response["content"],
            "tool_calls": response["tool_calls"],
            "tool_results": response["tool_results"]
        }
```

### 10.5 Chạy với Ollama

**Step 1: Start Ollama**
```bash
# Terminal 1
ollama serve

# Pull model if needed
ollama pull codellama
```

**Step 2: Start Blender MCP Server**
```bash
# Terminal 2
blender --background --python server/websocket_server.py
```

**Step 3: Test với Ollama**
```python
# test_ollama.py
from ollama_blender_config import OllamaBlenderAssistant

assistant = OllamaBlenderAssistant(model="codellama")

# Test natural language
response = assistant.execute("Create 5 cubes in a circle")
print(response["content"])
print(response["tool_calls"])
```

### 10.6 So sánh các LLM Options

| Feature | Ollama (Local) | Claude | GPT-4 |
|---------|----------------|--------|-------|
| **Cost** | Free | $15-60/million tokens | $10-30/million tokens |
| **Privacy** | ✅ 100% local | ❌ Cloud | ❌ Cloud |
| **Speed** | ⚡ Fast (local) | 🐢 Network dependent | 🐢 Network dependent |
| **Quality** | Good (7-8/10) | Excellent (9/10) | Excellent (9/10) |
| **Setup** | Medium | Easy | Easy |
| **Offline** | ✅ Yes | ❌ No | ❌ No |
| **Customizable** | ✅ Full | ❌ Limited | ❌ Limited |

### 10.7 Recommended Models for Blender

| Model | Size | Quality | Speed | Use Case |
|-------|------|---------|-------|----------|
| **CodeLlama** | 7B-34B | ⭐⭐⭐⭐ | Fast | Code generation, tool calls |
| **Llama2** | 7B-70B | ⭐⭐⭐⭐ | Medium | General assistance |
| **Mistral** | 7B | ⭐⭐⭐⭐ | Fast | Good balance |
| **Mixtral** | 8x7B | ⭐⭐⭐⭐⭐ | Medium | Best quality local |

### 10.8 Example Prompts for Ollama

```python
prompts = [
    # Scene creation
    "Create a simple house with a roof, door, and two windows",

    # Animation
    "Make the cube bounce from left to right over 30 frames",

    # Lighting
    "Add three-point lighting to the scene",

    # Camera
    "Position the camera to view all objects from above",

    # Materials
    "Apply a red metallic material to the sphere",

    # Complex scene
    "Create a chessboard with all pieces in starting positions"
]
```

---

## 11. Kết luận

### 11.1 Summary

Blender MCP + Bot integration là **khả thi và giá trị cao**:

✅ **Technical feasibility:** Python API mạnh, kiến trúc mở
✅ **LLM options:** Claude, GPT-4, **Ollama local**
✅ **Use cases:** Automation, AI-assisted modeling, batch processing
✅ **Community:** Large, active Blender community

### 11.2 Recommended Stack

**Production:**
- Claude/GPT-4 cho quality cao nhất
- WebSocket transport
- API key authentication

**Development/Privacy:**
- **Ollama local (CodeLlama/Mistral)**
- No API costs
- Full privacy
- Offline capable

### 11.3 Next Steps

1. **Setup Ollama:** `brew install ollama && ollama pull codellama`
2. **Test integration:** Run `ollama_blender_config.py`
3. **Customize prompts:** Add workflow-specific templates
4. **Deploy:** Start with local, scale to cloud if needed

---

## 10. Tài liệu Tham khảo

### Blender API

- [bpy.types.Module](https://docs.blender.org/api/current/bpy.types.Module.html)
- [bpy.ops Module](https://docs.blender.org/api/current/bpy.ops.html)
- [bpy.app Module](https://docs.blender.org/api/current/bpy.app.html)
- [Application Handlers](https://docs.blender.org/api/current/bpy.app.handlers.html)

### MCP

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

### Related Projects

- [Blender-LLM](https://github.com/AntonOsika/blender-gpt) - GPT integration
- [bpy-remote](https://github.com/ahujasid/blender-mcp) - Remote Blender control
- [Blender HTTP API](https://github.com/eliemichel/BlenderHTTPAPI) - HTTP server addon

---

## Phụ lục A: Quick Start Guide

### Cài đặt MCP Server

```bash
# 1. Clone repository
git clone https://github.com/your-org/blender-mcp.git
cd blender-mcp

# 2. Install dependencies
pip install mcp websockets

# 3. Install as Blender addon
# Copy to Blender addons directory
cp -r mcp_blender_addon ~/.config/blender/4.0/scripts/addons/

# 4. Enable addon in Blender
# Edit > Preferences > Add-ons > Search "MCP" > Enable

# 5. Start server
# In Blender: View3D > Sidebar > MCP > Start Server
```

### Test với Claude

```bash
# Configure Claude Desktop
# ~/.config/claude/claude_desktop_config.json

{
  "mcpServers": {
    "blender": {
      "command": "python",
      "args": ["/path/to/mcp_blender_server.py"],
      "env": {}
    }
  }
}
```

### Example Prompts

```
"Create a simple house with a roof and door"

"Animate a camera flying through the scene"

"Create 100 random trees in a forest pattern"

"Export all objects as separate OBJ files"

"Apply a red glossy material to the selected object"
```

---

**Document Version:** 1.0
**Last Updated:** March 2026
**Author:** AI Assistant

---

## 12. Hướng dẫn Build và Đóng gói Ứng dụng

### 12.1 Tổng quan

Hướng dẫn này mô tả quy trình build và đóng gói Blender MCP Server cho:
- **Windows 64-bit** (.msi installer)
- **macOS Silicon** (.dmg installer)

### 12.2 Chuẩn bị

#### Yêu cầu chung

| Component | Version | Ghi chú |
|-----------|---------|---------|
| Python | 3.11+ | Same version as Blender |
| Node.js | 18+ | For web interface |
| Git | Latest | Version control |

#### Cấu trúc project

```
blender-mcp/
├── src/                          # Source code
│   ├── server/
│   ├── llm/
│   ├── prompts/
│   └── web_interface/
├── addon/                        # Blender addon
├── build/                        # Build scripts
│   ├── windows/
│   │   ├── installer.wxs
│   │   └── build.ps1
│   └── macos/
│       ├── entitlements.plist
│       └── build.sh
├── dist/                         # Output packages
└── requirements.txt
```

---

## A. Windows 64-bit MSI Build

### A.1 Yêu cầu

```powershell
# Install Python
winget install Python.Python.3.11

# Install WiX Toolset (for MSI)
winget install WixToolset.WixToolset

# Install Node.js (optional, for web UI)
winget install OpenJS.NodeJS.LTS
```

### A.2 Chuẩn bị môi trường

```powershell
# Create project directory
mkdir C:\dev\blender-mcp
cd C:\dev\blender-mcp

# Clone repository
git clone https://github.com/your-org/blender-mcp.git .

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller cx_Freeze
```

### A.3 Tạo executable với PyInstaller

**File: `build/windows/pyinstaller_spec.py`**

```python
# PyInstaller spec file for Blender MCP Server
from PyInstaller.utils.hooks import collect_submodules
import os

project_root = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(project_root, '..', '..', 'src')

a = Analysis(
    [os.path.join(src_dir, 'server', 'websocket_server.py')],
    pathex=[src_dir],
    binaries=[],
    datas=[
        (os.path.join(src_dir, 'web_interface', 'index.html'), 'web_interface'),
        (os.path.join(src_dir, '..', 'requirements.txt'), '.'),
    ],
    hiddenimports=[
        'websockets',
        'aiohttp',
        'requests',
        'anthropic',
        'openai',
    ] + collect_submodules('bpy'),
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BlenderMCPServer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'icon.ico'),
)
```

**Chạy build:**

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Build executable
pyinstaller build/windows/pyinstaller_spec.py --clean

# Output will be in dist/BlenderMCPServer.exe
```

### A.4 Tạo WiX Installer

**File: `build/windows/installer.wxs`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*" 
           Name="Blender MCP Server" 
           Language="1033" 
           Version="1.0.0" 
           Manufacturer="Blender MCP Team" 
           UpgradeCode="PUT-YOUR-UPGRADE-CODE-HERE">
    
    <Package InstallerVersion="200" 
             Compressed="yes" 
             InstallScope="perMachine" 
             Description="Blender MCP Server Installer"/>
    
    <MajorUpgrade DowngradeErrorMessage="A newer version of [ProductName] is already installed."/>
    <MediaTemplate EmbedCab="yes"/>
    
    <!-- Features -->
    <Feature Id="MainApplication" Title="Blender MCP Server" Level="1">
      <ComponentGroupRef Id="ProductComponents"/>
      <ComponentRef Id="ApplicationShortcut"/>
    </Feature>
    
    <!-- UI -->
    <UI>
      <UIRef Id="WixUI_InstallDir"/>
    </UI>
    <Property Id="WIXUI_INSTALLDIR" Value="INSTALLFOLDER"/>
    
    <!-- Directory Structure -->
    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFiles64Folder">
        <Directory Id="INSTALLFOLDER" Name="Blender MCP Server">
          
          <!-- Main executable -->
          <Component Id="MainExe" Guid="*">
            <File Id="MainExeFile" 
                  Source="$(var.BuildDir)\dist\BlenderMCPServer.exe" 
                  KeyPath="yes"/>
          </Component>
          
          <!-- Python dependencies -->
          <Component Id="PythonDeps" Guid="*">
            <File Id="RequirementsFile" 
                  Source="$(var.BuildDir)\requirements.txt" 
                  KeyPath="yes"/>
          </Component>
          
          <!-- Web interface -->
          <Directory Id="WebInterface" Name="web_interface">
            <Component Id="WebUI" Guid="*">
              <File Id="IndexHtml" 
                    Source="$(var.BuildDir)\src\web_interface\index.html" 
                    KeyPath="yes"/>
            </Component>
          </Directory>
          
        </Directory>
      </Directory>
      
      <!-- Start Menu Shortcut -->
      <Directory Id="ProgramMenuFolder">
        <Directory Id="ApplicationProgramsFolder" Name="Blender MCP Server">
          <Component Id="ApplicationShortcut" Guid="*">
            <Shortcut Id="ApplicationStartMenuShortcut"
                      Name="Blender MCP Server"
                      Description="Blender MCP Server"
                      Target="[INSTALLFOLDER]BlenderMCPServer.exe"
                      WorkingDirectory="INSTALLFOLDER"/>
            <RemoveFolder Id="ApplicationProgramsFolder" On="uninstall"/>
            <RegistryValue Root="HKCU"
                          Key="Software\BlenderMCP"
                          Name="installed"
                          Type="integer"
                          Value="1"
                          KeyPath="yes"/>
          </Component>
        </Directory>
      </Directory>
    </Directory>
    
    <!-- Environment Variables -->
    <Component Id="SetEnvironment" Guid="*" Directory="INSTALLFOLDER">
      <Environment Id="PATH" 
                   Name="PATH" 
                   Value="[INSTALLFOLDER]" 
                   Permanent="no" 
                   Part="last" 
                   Action="set" 
                   System="yes"/>
    </Component>
    
  </Product>
</Wix>
```

### A.5 Build MSI với WiX

**File: `build/windows/build.ps1`**

```powershell
# Build script for Windows MSI
param(
    [string]$Version = "1.0.0",
    [string]$OutputDir = "..\..\dist\windows",
    [switch]$SignCode
)

$ErrorActionPreference = "Stop"

Write-Host "=== Blender MCP Server Windows Build ===" -ForegroundColor Cyan
Write-Host "Version: $Version"
Write-Host ""

# Step 1: Setup
Write-Host "[1/6] Setting up environment..." -ForegroundColor Yellow
$BuildDir = Get-Location
$ProjectRoot = $BuildDir.Parent.Parent.FullName

# Step 2: Install Python dependencies
Write-Host "[2/6] Installing Python dependencies..." -ForegroundColor Yellow
pip install -r "$ProjectRoot\requirements.txt" --quiet
pip install pyinstaller --quiet

# Step 3: Build executable with PyInstaller
Write-Host "[3/6] Building executable with PyInstaller..." -ForegroundColor Yellow
pyinstaller "$BuildDir\pyinstaller_spec.py" --clean --distpath "$BuildDir\dist"

# Step 4: Compile WiX source
Write-Host "[4/6] Compiling WiX source..." -ForegroundColor Yellow
$candleExe = "candle.exe"
$lightExe = "light.exe"

& $candleExe -dBuildDir="$BuildDir" -dVersion="$Version" `
    -out "$BuildDir\installer.wixobj" `
    "$BuildDir\installer.wxs"

if ($LASTEXITCODE -ne 0) {
    throw "WiX compilation failed"
}

# Step 5: Build MSI
Write-Host "[5/6] Building MSI installer..." -ForegroundColor Yellow
$MsiPath = "$OutputDir\BlenderMCP-Server-$Version-x64.msi"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

& $lightExe -out $MsiPath "$BuildDir\installer.wixobj"

if ($LASTEXITCODE -ne 0) {
    throw "MSI build failed"
}

# Step 6: Code signing (optional)
if ($SignCode) {
    Write-Host "[6/6] Signing MSI..." -ForegroundColor Yellow
    $signtool = "C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe"
    & $signtool sign /f "certificate.pfx" /p $env:SignPassword $MsiPath
}

# Summary
Write-Host ""
Write-Host "=== Build Complete ===" -ForegroundColor Green
Write-Host "Output: $MsiPath"
Write-Host "Size: $((Get-Item $MsiPath).Length / 1MB) MB"
```

### A.6 Chạy build

```powershell
cd build\windows
.\build.ps1 -Version "1.0.0" -SignCode:$false

# Output: dist/windows/BlenderMCP-Server-1.0.0-x64.msi
```

### A.7 Silent Installation

```powershell
# Silent install
msiexec /i BlenderMCP-Server-1.0.0-x64.msi /quiet

# Install with custom directory
msiexec /i BlenderMCP-Server-1.0.0-x64.msi /quiet INSTALLDIR="C:\Apps\BlenderMCP"

# Uninstall
msiexec /x {PRODUCT-CODE} /quiet
```

---

## B. macOS Silicon (ARM64) DMG Build

### B.1 Yêu cầu

```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Python (ARM64)
brew install python@3.11

# Install create-dmg
brew install create-dmg

# Install codesign tools (optional, for notarization)
# Need Apple Developer ID
```

### B.2 Chuẩn bị môi trường

```bash
# Create project directory
mkdir ~/dev/blender-mcp
cd ~/dev/blender-mcp

# Clone repository
git clone https://github.com/your-org/blender-mcp.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller py2app
```

### B.3 Tạo App Bundle với PyInstaller

**File: `build/macos/pyinstaller_spec.py`**

```python
# PyInstaller spec for macOS
from PyInstaller.utils.hooks import collect_submodules
import os
import plistlib

project_root = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(project_root, '..', '..', 'src')

# App info
APP_NAME = 'Blender MCP Server'
BUNDLE_ID = 'com.blender.mcp.server'
VERSION = '1.0.0'

a = Analysis(
    [os.path.join(src_dir, 'server', 'websocket_server.py')],
    pathex=[src_dir],
    binaries=[],
    datas=[
        (os.path.join(src_dir, 'web_interface', 'index.html'), 'web_interface'),
        (os.path.join(src_dir, '..', 'requirements.txt'), '.'),
    ],
    hiddenimports=[
        'websockets',
        'aiohttp',
        'requests',
        'anthropic',
        'openai',
    ] + collect_submodules('bpy'),
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',  # Silicon
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'icon.icns'),
)

# Create app bundle
app = BUNDLE(
    exe,
    name=f'{APP_NAME}.app',
    icon=exe.icon,
    bundle_identifier=BUNDLE_ID,
    version=VERSION,
    info_plist={
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleIdentifier': BUNDLE_ID,
        'CFBundleVersion': VERSION,
        'CFBundleShortVersionString': VERSION,
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'CFBundleExecutable': os.path.basename(exe.name),
        'NSHighResolutionCapable': 'True',
        'LSMinimumSystemVersion': '12.0',  # macOS Monterey
        'LSArchitecturePriority': ['arm64'],
    }
)
```

### B.4 Entitlements File

**File: `build/macos/entitlements.plist`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- App Sandbox -->
    <key>com.apple.security.app-sandbox</key>
    <false/>
    
    <!-- Network -->
    <key>com.apple.security.network.server</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
    
    <!-- Files -->
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
    
    <!-- Python scripting -->
    <key>com.apple.security.scripting-targets</key>
    <true/>
    
    <!-- Hardened Runtime -->
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
</dict>
</plist>
```

### B.5 Build Script

**File: `build/macos/build.sh`**

```bash
#!/bin/bash
set -e

# Configuration
VERSION=${1:-"1.0.0"}
OUTPUT_DIR="../../dist/macos"
APP_NAME="Blender MCP Server"
BUNDLE_ID="com.blender.mcp.server"

echo "=== Blender MCP Server macOS Build ==="
echo "Version: $VERSION"
echo ""

# Colors
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Step 1: Setup
echo -e "${YELLOW}[1/7] Setting up environment...${NC}"
BUILD_DIR=$(pwd)
PROJECT_ROOT=$(cd "$BUILD_DIR/../.." && pwd)

# Step 2: Install dependencies
echo -e "${YELLOW}[2/7] Installing Python dependencies...${NC}"
pip install -r "$PROJECT_ROOT/requirements.txt" --quiet
pip install pyinstaller --quiet

# Step 3: Build with PyInstaller
echo -e "${YELLOW}[3/7] Building app bundle with PyInstaller...${NC}"
pyinstaller "$BUILD_DIR/pyinstaller_spec.py" --clean

# Step 4: Codesign (if certificate available)
echo -e "${YELLOW}[4/7] Code signing...${NC}"
if security find-identity -v -p codesigning | grep -q "Developer ID"; then
    CERT=$(security find-identity -v -p codesigning | grep "Developer ID" | head -1 | awk -F'"' '{print $2}')
    echo "Using certificate: $CERT"
    
    codesign --force --deep --sign "$CERT" \
        --entitlements "$BUILD_DIR/entitlements.plist" \
        "$BUILD_DIR/dist/$APP_NAME.app"
    
    echo "✓ Code signed"
else
    echo "⚠ No signing certificate found, skipping codesign"
fi

# Step 5: Create DMG
echo -e "${YELLOW}[5/7] Creating DMG installer...${NC}"
mkdir -p "$OUTPUT_DIR"

DMG_PATH="$OUTPUT_DIR/${APP_NAME}-$VERSION-Silicon.dmg"

# Remove old DMG
rm -f "$DMG_PATH"

# Create DMG with create-dmg
if command -v create-dmg &> /dev/null; then
    create-dmg \
        --volname "$APP_NAME" \
        --volicon "$BUILD_DIR/icon.icns" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "$APP_NAME.app" 150 150 \
        --app-drop-link 450 150 \
        --hide-extension "$APP_NAME.app" \
        "$DMG_PATH" \
        "$BUILD_DIR/dist/$APP_NAME.app"
else
    # Fallback: simple DMG creation
    hdiutil create -volname "$APP_NAME" -srcfolder "$BUILD_DIR/dist/$APP_NAME.app" \
        -ov -format UDZO "$DMG_PATH"
fi

echo "✓ DMG created: $DMG_PATH"

# Step 6: Notarization (optional, requires Apple ID)
echo -e "${YELLOW}[6/7] Notarization...${NC}"
if [ -n "$APPLE_ID" ] && [ -n "$APPLE_APP_PASSWORD" ]; then
    echo "Submitting for notarization..."
    
    xcrun notarytool submit "$DMG_PATH" \
        --apple-id "$APPLE_ID" \
        --password "$APPLE_APP_PASSWORD" \
        --team-id "$TEAM_ID" \
        --wait
    
    # Staple notarization ticket
    xcrun stapler staple "$DMG_PATH"
    echo "✓ Notarized"
else
    echo "⚠ No Apple ID credentials, skipping notarization"
fi

# Step 7: Verify
echo -e "${YELLOW}[7/7] Verifying build...${NC}"
echo "DMG Size: $(du -h "$DMG_PATH" | cut -f1)"
echo "Contents:"
ls -la "$OUTPUT_DIR"

# Summary
echo ""
echo -e "${GREEN}=== Build Complete ===${NC}"
echo "Output: $DMG_PATH"
echo ""
echo "Installation:"
echo "  1. Open $DMG_PATH"
echo "  2. Drag $APP_NAME.app to Applications"
echo "  3. Run from Applications folder"
```

### B.6 Chạy build

```bash
cd build/macos
chmod +x build.sh

# Basic build
./build.sh 1.0.0

# With notarization (set env vars first)
export APPLE_ID="your@apple.id"
export APPLE_APP_PASSWORD="app-specific-password"
export TEAM_ID="YOUR_TEAM_ID"
./build.sh 1.0.0
```

### B.7 Universal Binary (Intel + Silicon)

**File: `build/macos/build_universal.sh`**

```bash
#!/bin/bash
# Build universal binary for both Intel and Apple Silicon

set -e

VERSION=${1:-"1.0.0"}
BUILD_DIR=$(pwd)
DIST_DIR="$BUILD_DIR/dist"

echo "=== Building Universal Binary ==="

# Build for Intel (x86_64)
echo "[1/3] Building Intel binary..."
arch -x86_64 pyinstaller "$BUILD_DIR/pyinstaller_spec.py" \
    --clean \
    --target-arch=x86_64 \
    --distpath "$DIST_DIR/intel"

# Build for Silicon (arm64)
echo "[2/3] Building Silicon binary..."
arch -arm64 pyinstaller "$BUILD_DIR/pyinstaller_spec.py" \
    --clean \
    --target-arch=arm64 \
    --distpath "$DIST_DIR/silicon"

# Merge binaries
echo "[3/3] Creating universal binary..."
lipo -create \
    "$DIST_DIR/intel/Blender MCP Server/Blender MCP Server" \
    "$DIST_DIR/silicon/Blender MCP Server/Blender MCP Server" \
    -output "$DIST_DIR/universal/Blender MCP Server/Blender MCP Server"

echo "✓ Universal binary created"
```

---

## C. CI/CD Automation

### C.1 GitHub Actions Workflow

**File: `.github/workflows/build.yml`**

```yaml
name: Build Installers

on:
  push:
    tags:
      - 'v*.*.*'
  workflow_dispatch:

jobs:
  build-windows:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pyinstaller
    
    - name: Build MSI
      run: |
        cd build/windows
        .\build.ps1 -Version ${{ github.ref_name }}
    
    - name: Upload artifact
      uses: actions/upload-artifact@v4
      with:
        name: windows-installer
        path: dist/windows/*.msi

  build-macos:
    runs-on: macos-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pyinstaller
        brew install create-dmg
    
    - name: Build DMG
      run: |
        cd build/macos
        ./build.sh ${{ github.ref_name }}
    
    - name: Upload artifact
      uses: actions/upload-artifact@v4
      with:
        name: macos-installer
        path: dist/macos/*.dmg

  release:
    needs: [build-windows, build-macos]
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Download artifacts
      uses: actions/download-artifact@v4
    
    - name: Create Release
      uses: softprops/action-gh-release@v1
      with:
        files: |
          windows-installer/*.msi
          macos-installer/*.dmg
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## D. Testing và Verification

### D.1 Windows Testing

```powershell
# Test installation
msiexec /i dist/windows/BlenderMCP-Server-1.0.0-x64.msi /quiet /norestart

# Verify installation
Test-Path "C:\Program Files\Blender MCP Server\BlenderMCPServer.exe"

# Test execution
& "C:\Program Files\Blender MCP Server\BlenderMCPServer.exe" --help

# Test uninstallation
msiexec /x {PRODUCT-CODE} /quiet
```

### D.2 macOS Testing

```bash
# Test DMG
hdiutil attach dist/macos/Blender\ MCP\ Server-1.0.0-Silicon.dmg

# Verify app bundle
ls -la /Volumes/Blender\ MCP\ Server/

# Test execution
/Volumes/Blender\ MCP\ Server/Blender\ MCP\ Server.app/Contents/MacOS/Blender\ MCP\ Server --help

# Detach
hdiutil detach /Volumes/Blender\ MCP\ Server
```

### D.3 Code Signing Verification

**Windows:**
```powershell
# Verify signature
signtool verify /pa "dist/windows/BlenderMCP-Server-1.0.0-x64.msi"
```

**macOS:**
```bash
# Verify signature
codesign --verify --verbose dist/macos/Blender\ MCP\ Server-1.0.0-Silicon.dmg

# Check notarization
spctl --assess --type install dist/macos/Blender\ MCP\ Server-1.0.0-Silicon.dmg
```

---

## E. Distribution

### E.1 Release Checklist

- [ ] Build Windows MSI (x64)
- [ ] Build macOS DMG (Silicon + Universal option)
- [ ] Code sign all installers
- [ ] Notarize macOS installer
- [ ] Test on clean VMs
- [ ] Upload to GitHub Releases
- [ ] Update documentation
- [ ] Announce release

### E.2 System Requirements

**Windows:**
- Windows 10/11 (64-bit)
- Python 3.11+ (or use bundled)
- Blender 4.0+
- 500MB free space

**macOS:**
- macOS 12.0+ (Monterey or later)
- Apple Silicon (M1/M2/M3) or Intel
- Python 3.11+ (or use bundled)
- Blender 4.0+
- 500MB free space

---

## F. Troubleshooting

### F.1 Common Issues

**Windows:**

| Issue | Solution |
|-------|----------|
| MSI build fails | Check WiX Toolset installation |
| Missing DLLs | Add to PyInstaller hiddenimports |
| Code sign fails | Check certificate validity |

**macOS:**

| Issue | Solution |
|-------|----------|
| App won't open | Codesign with valid certificate |
| Notarization fails | Check entitlements.plist |
| Universal binary fails | Ensure both archs build separately |

### F.2 Debug Build

**Windows:**
```powershell
.\build.ps1 -Version "1.0.0-dev" -SignCode:$false
```

**macOS:**
```bash
# Skip codesign and notarization
./build.sh 1.0.0-dev
```

---

## G. Summary

### Build Outputs

| Platform | Output | Size | Time |
|----------|--------|------|------|
| Windows x64 | .msi | ~50MB | 5-10 min |
| macOS Silicon | .dmg | ~45MB | 5-8 min |
| macOS Universal | .dmg | ~80MB | 10-15 min |

### Next Steps

1. **Automate:** Setup GitHub Actions CI/CD
2. **Sign:** Get code signing certificates
3. **Test:** Test on clean VMs
4. **Distribute:** GitHub Releases, Homebrew, winget

---

**Build Complete!** 🎉
