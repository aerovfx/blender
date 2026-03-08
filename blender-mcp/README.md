# Blender MCP Server

Model Context Protocol (MCP) server for Blender automation and AI-assisted 3D workflows.

## 🎯 Features

### Phase 1: Core Functionality ✅
- 🎨 **Core 3D Operations**: Create, modify, delete objects
- 🔌 **Multiple Transports**: stdio (MCP), WebSocket
- 🔒 **Security**: API key authentication, rate limiting
- 📦 **Blender Addon**: Built-in UI panel

### Phase 2: Advanced Tools + LLM ✅
- 🦴 **Rigging Tools**: Humanoid rigs, mechanical rigs, auto weight paint
- 🎬 **Animation**: Keyframing, camera animation, bouncing ball
- 📦 **Batch Processing**: Export/import multiple, cleanup
- 🔷 **Geometry Nodes**: Add modifiers, procedural modeling
- 🤖 **LLM Integration**: Claude, GPT-4, Ollama support
- 📝 **Prompt Templates**: Pre-built automation templates
- 🌐 **Web Interface**: Browser-based control panel
- 💭 **Context Management**: Multi-turn conversations

---

## Quick Start

### Installation

```bash
cd /Users/pixibox/blender/blender-mcp
pip install -r requirements.txt
```

### Start WebSocket Server

```bash
blender --background --python server/websocket_server.py
```

### Test Connection

```bash
python examples/test_server.py
```

### Web Interface

```bash
python web_interface/server.py
# Open http://localhost:8080
```

---

## Usage Examples

### Basic Object Creation

```python
import websocket, json

ws = websocket.create_connection("ws://localhost:8765")

# Create a cube
ws.send(json.dumps({
    "type": "request",
    "id": 1,
    "method": "create_object",
    "params": {"type": "cube", "location": [0, 0, 0]}
}))

print(json.loads(ws.recv()))
```

### With LLM (Natural Language)

```python
from llm.llm_integration import create_blender_assistant

assistant = create_blender_assistant(
    provider="claude",
    api_key="your-api-key"
)

# Natural language to Blender
assistant.execute("Create a cityscape with 10 buildings")
assistant.execute("Now add a red sphere in the center")
assistant.execute("Animate the camera orbiting around")
```

### Using Templates

```python
from prompts.prompt_templates import render_prompt
from llm.llm_integration import create_blender_assistant

prompt = render_prompt(
    "simple_scene",
    object_count=5,
    object_type="cube",
    arrangement="circle"
)

assistant = create_blender_assistant(provider="claude")
assistant.execute(prompt)
```

---

## Available Tools

### Core Tools
| Tool | Description |
|------|-------------|
| `create_object` | Create primitives (cube, sphere, cylinder, etc.) |
| `delete_object` | Delete an object |
| `modify_object` | Transform (location, rotation, scale) |
| `get_scene_info` | Get scene state |
| `set_material` | Apply/create materials |
| `create_camera` | Add camera |
| `create_light` | Add light |
| `render_scene` | Render to file |
| `export_file` | Export formats (FBX, OBJ, GLTF) |

### Advanced Tools (Phase 2)
| Tool | Description |
|------|-------------|
| `create_humanoid_rig` | Create character rig |
| `auto_weight_paint` | Auto weight painting |
| `animate_location` | Position keyframes |
| `create_bouncing_ball_animation` | Bouncing ball |
| `create_camera_animation` | Camera animations |
| `batch_export` | Export multiple objects |
| `cleanup_unused_data` | Clean scene |
| `add_geometry_nodes_modifier` | Add GeoNodes |

---

## LLM Integration

### Supported Providers

| Provider | Models | Setup |
|----------|--------|-------|
| **Claude** | claude-3-5-sonnet, etc. | `export ANTHROPIC_API_KEY=...` |
| **GPT-4** | gpt-4-turbo, gpt-4o | `export OPENAI_API_KEY=...` |
| **Ollama** | llama2, mistral, etc. | Local, no key needed |

### Example Prompts

```
"Create a product showcase with white backdrop and three-point lighting"

"Make a solar system with all planets orbiting the sun"

"Create a room interior with furniture and animate a walkthrough"

"Rig this character and make it walk forward"
```

---

## Project Structure

```
blender-mcp/
├── server/
│   ├── mcp_server.py           # MCP stdio (Claude Desktop)
│   ├── websocket_server.py     # WebSocket server
│   ├── tools.py                # Core tools
│   └── advanced/
│       └── tools_advanced.py   # Advanced tools
├── llm/
│   ├── llm_integration.py      # LLM providers
│   └── context_manager.py      # Conversation context
├── prompts/
│   └── prompt_templates.py     # Template library
├── web_interface/
│   ├── index.html              # Web UI
│   └── server.py               # Web server
├── addon/
│   └── __init__.py             # Blender addon
├── examples/
│   ├── basic_usage.py
│   ├── advanced.py
│   └── test_server.py
└── docs/
    ├── api.md
    ├── quickstart.md
    └── PHASE2.md
```

---

## Configuration

### Claude Desktop Integration

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "blender": {
      "command": "blender",
      "args": [
        "--background",
        "--python",
        "/Users/pixibox/blender/blender-mcp/server/mcp_server.py"
      ]
    }
  }
}
```

### Blender Addon

1. Copy addon to Blender:
```bash
cp -r addon ~/Library/Application\ Support/Blender/4.0/scripts/addons/blender_mcp
```

2. Enable in Blender: `Edit > Preferences > Add-ons > Search "MCP"`

3. Access via: View3D > Sidebar > MCP Server

---

## Documentation

- **[Quick Start](docs/quickstart.md)** - Getting started guide
- **[API Reference](docs/api.md)** - Complete API documentation
- **[Phase 2 Features](docs/PHASE2.md)** - Advanced tools and LLM integration

---

## Requirements

- **Blender:** 4.0+
- **Python:** 3.11+
- **Dependencies:** See `requirements.txt`

---

## License

GPL-2.0-or-later (same as Blender)

---

## Roadmap

- [x] Phase 1: Core MCP Server + Addon
- [x] Phase 2: Advanced Tools + LLM Integration
- [ ] Phase 3: Multi-user + Cloud Deployment
- [ ] Phase 4: Voice Control + Plugin Marketplace

---

## Contributing

Contributions welcome! Please read the documentation and submit PRs.

## Support

- Issues: GitHub Issues
- Discussion: GitHub Discussions
- Documentation: `/docs` folder
