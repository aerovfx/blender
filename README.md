# Blender Automation & Procedural Workflow

**Blender MCP Server - AI-Powered Automation & Procedural Generation**

Một hệ thống tự động hóa và xây dựng quy trình procedural tối ưu cho Blender 3D, sử dụng AI/LLM và Model Context Protocol (MCP).

---

## 🎯 Mục Tiêu

### Tự Động Hóa Blender
- 🤖 **AI-Assisted Modeling**: Tạo và chỉnh sửa 3D objects bằng ngôn ngữ tự nhiên
- ⚡ **Batch Processing**: Tự động hóa các tác vụ lặp đi lặp lại
- 🔧 **Procedural Workflow**: Xây dựng quy trình procedural tối ưu
- 🌐 **Remote Control**: Điều khiển Blender từ xa qua WebSocket/API

### Xây Dựng Procedural Pipeline
- 📐 **Geometry Nodes**: Tạo assets procedural phức tạp
- 🔄 **Node-Based Workflow**: Thiết kế workflow dựa trên nodes
- 🎬 **Animation Automation**: Tự động tạo animation sequences
- 🎨 **Material Generation**: Tạo materials tự động

---

## 🚀 Quick Start

### 1. Cài Đặt

```bash
cd blender-mcp
pip install -r requirements.txt
```

### 2. Chạy Server

```bash
# WebSocket Server (cho web clients và custom apps)
blender --background --python server/websocket_server.py

# MCP Server (cho Claude Desktop, LLM clients)
blender --background --python server/mcp_server.py
```

### 3. Test Kết Nối

```bash
python examples/test_server.py
```

### 4. Web Interface

```bash
python web_interface/server.py
# Open http://localhost:8080
```

---

## 📋 Nội Dung

### [📖 Documentation](docs/)
- **[Quick Start Guide](docs/quickstart.md)** - Bắt đầu nhanh
- **[API Reference](docs/api.md)** - API đầy đủ
- **[Phase 2 Features](docs/PHASE2.md)** - Advanced tools & LLM
- **[Build Guide](cmake_guide.md)** - Build MSI/DMG installers

### [🤖 LLM Integration](llm/)
- **Claude** - Anthropic API
- **GPT-4** - OpenAI API
- **Ollama** - Local LLM (privacy, offline)

### [📝 Prompt Templates](prompts/)
- Scene creation templates
- Animation templates
- Rigging templates
- Material templates
- Batch processing templates

### [🛠️ Tools](server/)
- **Core Tools**: Create, modify, delete objects
- **Advanced Tools**: Rigging, animation, batch processing, Geometry Nodes
- **Security**: API keys, rate limiting, authentication

### [🌐 Web Interface](web_interface/)
- Chat-based control panel
- Quick action buttons
- Scene viewer
- Activity log

### [📦 Blender Addon](addon/)
- UI panel trong Blender
- Start/stop server
- Configuration settings

---

## 🎨 Use Cases

### 1. AI-Assisted Modeling

```python
# Tự động tạo cảnh bằng ngôn ngữ tự nhiên
assistant.execute("Create a cityscape with 10 buildings of varying heights")
assistant.execute("Add a red sphere at position (5, 0, 0)")
assistant.execute("Create a camera looking at the origin")
```

### 2. Procedural Asset Generation

```python
# Tạo assets procedural với Geometry Nodes
ws.send(json.dumps({
    "method": "geo_nodes_scatter",
    "params": {
        "base_object": "Terrain",
        "instance_object": "Tree",
        "count": 500,
        "distribution": "random"
    }
}))
```

### 3. Animation Automation

```python
# Tự động tạo animation
ws.send(json.dumps({
    "method": "create_bouncing_ball_animation",
    "params": {
        "object_name": "Ball",
        "start_frame": 1,
        "end_frame": 60,
        "bounce_count": 5
    }
}))
```

### 4. Batch Processing Pipeline

```python
# Export hàng loạt objects
ws.send(json.dumps({
    "method": "batch_export",
    "params": {
        "directory": "//exports",
        "format": "FBX",
        "individual_objects": True
    }
}))
```

### 5. Character Rigging

```python
# Tạo rig và auto weight paint
ws.send(json.dumps({
    "method": "create_humanoid_rig",
    "params": {"name": "CharacterRig", "height": 1.8}
}))
ws.send(json.dumps({
    "method": "auto_weight_paint",
    "params": {"mesh_object": "Character", "armature_object": "CharacterRig"}
}))
```

---

## 🔧 Procedural Workflow Examples

### Example 1: Procedural City Generator

```python
from llm.llm_integration import create_blender_assistant

assistant = create_blender_assistant(provider="ollama")

# Mô tả cảnh bằng ngôn ngữ tự nhiên
assistant.execute("""
Create a procedural city:
1. Generate a grid of 20x20 blocks
2. Create buildings with random heights (5-50 floors)
3. Add roads between blocks
4. Scatter trees and street lights
5. Set up camera for aerial view
""")
```

### Example 2: Animation Sequence

```python
# Tạo animation sequence với keyframes tự động
assistant.execute("""
Animate a camera fly-through:
1. Start camera at (0, -10, 5)
2. Move through the city center
3. Orbit around the tallest building
4. End at (0, 10, 5)
5. Duration: 120 frames at 24fps
""")
```

### Example 3: Material Library

```python
# Tạo material library tự động
materials = [
    {"name": "Concrete", "color": [0.5, 0.5, 0.5], "roughness": 0.9},
    {"name": "Glass", "color": [0.9, 0.95, 1.0], "transmission": 1.0},
    {"name": "Steel", "color": [0.8, 0.8, 0.8], "metallic": 1.0},
]

for mat in materials:
    ws.send(json.dumps({
        "method": "set_material",
        "params": mat
    }))
```

---

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Web UI      │  │ LLM Chat    │  │ Blender Addon       │  │
│  │ (Browser)   │  │ (Claude/GPT)│  │ (Sidebar Panel)     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server Layer                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Transport: WebSocket / Stdio (MCP)                  │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  LLM Integration: Claude, GPT-4, Ollama              │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Context Manager: Conversation History               │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Tool Execution Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Core Tools  │  │ Adv. Tools  │  │ Procedural Tools    │  │
│  │ - Create    │  │ - Rigging   │  │ - Geo Nodes         │  │
│  │ - Modify    │  │ - Animation │  │ - Scatter           │  │
│  │ - Delete    │  │ - Batch     │  │ - Procedural Gen    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Blender Python API                        │
│                    (bpy.ops, bpy.data, bpy.context)          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔒 Security

### Authentication
- API key authentication
- Optional authentication for local use
- Rate limiting (default: 100 req/min)

### Command Whitelist
```bash
# Restrict available commands
blender --background --python websocket_server.py -- \
  --allowed-commands create_object get_scene_info modify_object
```

### Safe Mode
```python
# Enable safe mode (read-only operations)
ws.send(json.dumps({
    "type": "request",
    "method": "set_safe_mode",
    "params": {"enabled": True}
}))
```

---

## 📦 Installation Options

### Option 1: Python Package
```bash
pip install -r requirements.txt
```

### Option 2: Blender Addon
```bash
# Copy to Blender addons
cp -r addon ~/.config/blender/4.0/scripts/addons/blender_mcp

# Enable in Blender: Edit > Preferences > Add-ons
```

### Option 3: Standalone Installer

**Windows:**
```powershell
# Download and run MSI installer
msiexec /i BlenderMCP-Server-1.0.0-x64.msi
```

**macOS:**
```bash
# Download DMG and drag to Applications
open BlenderMCP-Server-1.0.0-Silicon.dmg
```

---

## 🔗 Integration

### Claude Desktop

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "blender": {
      "command": "blender",
      "args": [
        "--background",
        "--python",
        "/path/to/mcp_server.py"
      ]
    }
  }
}
```

### Custom Applications

```python
import websocket
import json

ws = websocket.create_connection("ws://localhost:8765")

# Send command
ws.send(json.dumps({
    "type": "request",
    "id": 1,
    "method": "create_object",
    "params": {"type": "cube"}
}))

# Get response
response = json.loads(ws.recv())
```

---

## 🎓 Learning Resources

### Tutorials
1. **Getting Started** - Setup and basic usage
2. **LLM Integration** - Connect Claude, GPT-4, Ollama
3. **Procedural Workflows** - Geometry Nodes automation
4. **Animation Pipeline** - Auto-keyframing and sequences
5. **Batch Processing** - Export/import automation

### Example Projects
- `examples/basic_usage.py` - Basic operations
- `examples/advanced.py` - Advanced automation
- `examples/test_server.py` - Testing tools

---

## 🛠️ Development

### Build from Source

See [Build Guide](cmake_guide.md) for detailed instructions.

```bash
# Windows
cd build/windows
.\build.ps1 -Version "1.0.0"

# macOS
cd build/macos
./build.sh 1.0.0
```

### CI/CD

GitHub Actions workflow tự động build và release:

```yaml
# .github/workflows/build.yml
name: Build Installers
on:
  push:
    tags: ['v*.*.*']
```

---

## 📈 Roadmap

### Phase 1 ✅ - Core MCP Server
- WebSocket and stdio transport
- Core 3D operations
- Security features
- Blender addon

### Phase 2 ✅ - Advanced Tools + LLM
- Rigging and animation tools
- Batch processing
- Geometry Nodes
- LLM integration (Claude, GPT-4, Ollama)
- Prompt templates
- Web interface

### Phase 3 🚧 - Production Ready
- [ ] Multi-user collaboration
- [ ] Cloud deployment
- [ ] Advanced AI modeling
- [ ] Voice control
- [ ] Plugin marketplace

### Phase 4 📋 - Future
- [ ] Real-time collaboration
- [ ] VR/AR integration
- [ ] Machine learning models
- [ ] Asset library integration

---

## 🤝 Contributing

### Ways to Contribute
- 🐛 Report bugs
- 💡 Suggest features
- 📝 Improve documentation
- 🔧 Submit pull requests
- 🎨 Share templates

### Development Setup
```bash
git clone https://github.com/aerovfx/blender.git
cd blender
git checkout aerovfx_AI
pip install -r blender-mcp/requirements.txt
```

---

## 📄 License

GPL-2.0-or-later (same as Blender)

---

## 📞 Support

- **Issues:** https://github.com/aerovfx/blender/issues
- **Discussions:** https://github.com/aerovfx/blender/discussions
- **Documentation:** `/docs` folder

---

## 🙏 Acknowledgments

- Blender Foundation - https://www.blender.org
- Model Context Protocol - https://modelcontextprotocol.io
- Anthropic - Claude API
- OpenAI - GPT-4 API
- Ollama - Local LLM runtime

---

**Built with ❤️ for the Blender Community**

*Automating 3D workflows, one prompt at a time.*
