# Phase 2: Advanced Tools + LLM Integration

## Overview

Phase 2 extends the Blender MCP Server with advanced tools for professional workflows and integrates Large Language Models for natural language control.

**New Features:**
- 🦴 Advanced rigging tools (humanoid rigs, mechanical rigs)
- 🎬 Animation tools (keyframing, camera animation)
- 📦 Batch processing (export, import, cleanup)
- 🔷 Geometry Nodes manipulation
- 🤖 LLM integration (Claude, GPT-4, Ollama)
- 📝 Prompt templates library
- 🌐 Web-based control interface
- 💭 Conversation context management

---

## Installation

### Update Dependencies

```bash
cd /Users/pixibox/blender/blender-mcp
pip install -r requirements.txt
```

### New Dependencies

| Package | Purpose |
|---------|---------|
| `anthropic` | Claude API integration |
| `openai` | GPT-4 API integration |
| `aiohttp` | Web interface server |
| `requests` | HTTP requests for Ollama |

---

## Advanced Tools

### Rigging Tools

#### Create Humanoid Rig

```python
import websocket
import json

ws = websocket.create_connection("ws://localhost:8765")

# Create a full humanoid rig
ws.send(json.dumps({
    "type": "request",
    "id": 1,
    "method": "create_humanoid_rig",
    "params": {
        "name": "CharacterRig",
        "height": 1.8,
        "location": [0, 0, 0]
    }
}))

response = json.loads(ws.recv())
print(response)
```

#### Auto Weight Paint

```python
ws.send(json.dumps({
    "type": "request",
    "id": 2,
    "method": "auto_weight_paint",
    "params": {
        "mesh_object": "Character_Mesh",
        "armature_object": "CharacterRig"
    }
}))
```

### Animation Tools

#### Create Keyframes

```python
# Animate location
ws.send(json.dumps({
    "type": "request",
    "id": 3,
    "method": "animate_location",
    "params": {
        "object_name": "Ball",
        "keyframes": [
            {"frame": 1, "location": [0, 0, 5]},
            {"frame": 30, "location": [0, 0, 0]},
            {"frame": 60, "location": [10, 0, 5]}
        ]
    }
}))
```

#### Bouncing Ball Animation

```python
ws.send(json.dumps({
    "type": "request",
    "id": 4,
    "method": "create_bouncing_ball_animation",
    "params": {
        "object_name": "Ball",
        "start_frame": 1,
        "end_frame": 60,
        "bounce_height": 5.0,
        "bounces": 3
    }
}))
```

#### Camera Animation

```python
# Orbit animation
ws.send(json.dumps({
    "type": "request",
    "id": 5,
    "method": "create_camera_animation",
    "params": {
        "camera_name": "Camera",
        "animation_type": "orbit",
        "target_object": "Cube",
        "frames": 90
    }
}))
```

### Batch Processing

#### Batch Export

```python
ws.send(json.dumps({
    "type": "request",
    "id": 6,
    "method": "batch_export",
    "params": {
        "directory": "//exports",
        "format": "FBX",
        "individual_objects": True,
        "use_selection": False
    }
}))
```

#### Batch Apply Material

```python
ws.send(json.dumps({
    "type": "request",
    "id": 7,
    "method": "batch_apply_material",
    "params": {
        "material_name": "Gold",
        "object_type": "MESH"
    }
}))
```

#### Scene Cleanup

```python
ws.send(json.dumps({
    "type": "request",
    "id": 8,
    "method": "cleanup_unused_data",
    "params": {
        "materials": True,
        "meshes": True,
        "textures": True,
        "images": True
    }
}))
```

### Geometry Nodes

#### Add Geometry Nodes Modifier

```python
ws.send(json.dumps({
    "type": "request",
    "id": 9,
    "method": "add_geometry_nodes_modifier",
    "params": {
        "object_name": "Plane",
        "modifier_name": "Scatter"
    }
}))
```

#### Subdivide with Geo Nodes

```python
ws.send(json.dumps({
    "type": "request",
    "id": 10,
    "method": "geo_nodes_subdivide",
    "params": {
        "object_name": "Cube",
        "levels": 3
    }
}))
```

---

## LLM Integration

### Using Claude

```python
from llm.llm_integration import create_blender_assistant

# Create assistant with Claude
assistant = create_blender_assistant(
    provider="claude",
    api_key="your-anthropic-api-key",
    model="claude-3-5-sonnet-20241022"
)

# Execute natural language request
response = assistant.execute(
    "Create a cityscape with 10 buildings of varying heights"
)
print(response)
```

### Using GPT-4

```python
from llm.llm_integration import create_blender_assistant

# Create assistant with GPT-4
assistant = create_blender_assistant(
    provider="gpt",
    api_key="your-openai-api-key",
    model="gpt-4-turbo-preview"
)

response = assistant.execute(
    "Create a solar system with all planets"
)
```

### Using Local LLM (Ollama)

```python
from llm.llm_integration import create_blender_assistant

# Create assistant with local LLM
assistant = create_blender_assistant(
    provider="ollama",
    model="llama2",
    host="http://localhost:11434"
)

response = assistant.execute(
    "Add a red cube at the origin"
)
```

### With Conversation Context

```python
from llm.llm_integration import LLMManager
from llm.context_manager import ConversationContext, ContextAwareAssistant

# Create context manager
context = ConversationContext()

# Create LLM manager
llm = LLMManager(provider="claude", api_key="your-key")

# Create context-aware assistant
assistant = ContextAwareAssistant(
    llm_manager=llm,
    context=context,
    blender_tools=blender_tools
)

# Multi-turn conversation
response1 = assistant.process_message("Create a cube")
print(response1["response"])

response2 = assistant.process_message("Now move it to (5, 0, 0)")
print(response2["response"])  # "it" resolves to the cube
```

---

## Prompt Templates

### Using Templates

```python
from prompts.prompt_templates import render_prompt, get_prompt_library

# Get library
library = get_prompt_library()

# List available templates
templates = library.list_templates()
for t in templates:
    print(f"{t['name']}: {t['description']}")

# Render a template
prompt = render_prompt(
    "simple_scene",
    ground_material="concrete",
    object_count=5,
    object_type="cube",
    arrangement="circle",
    ground_color="[0.3, 0.3, 0.3]",
    object_color="[1, 0, 0]"
)

# Use with LLM
assistant.execute(prompt)
```

### Available Templates

| Category | Templates |
|----------|-----------|
| Scene Creation | Simple Scene, Product Showcase, Architectural Interior |
| Animation | Bouncing Ball, Camera Fly-through, Object Transformation |
| Rigging | Character Rig, Mechanical Rig |
| Materials | PBR Material, Glass Material |
| Batch | Batch Export, Scene Cleanup |
| Geometry Nodes | Scatter, Procedural Modeling |

---

## Web Interface

### Starting the Web Server

```bash
# Start Blender WebSocket server first
blender --background --python server/websocket_server.py

# Then start web interface
python web_interface/server.py
```

### Access the Interface

Open your browser to: `http://localhost:8080`

### Features

- 💬 Chat interface for natural language commands
- 🛠️ Quick action buttons for common operations
- 📋 Scene object viewer
- 📜 Activity log
- 🎨 Template selector

---

## Configuration

### Environment Variables

```bash
# For Claude
export ANTHROPIC_API_KEY="your-key"

# For GPT-4
export OPENAI_API_KEY="your-key"

# Optional: Custom API endpoint
export OLLAMA_HOST="http://localhost:11434"
```

### Configuration File

Create `config.json`:

```json
{
    "llm": {
        "provider": "claude",
        "model": "claude-3-5-sonnet-20241022"
    },
    "server": {
        "host": "localhost",
        "port": 8765,
        "require_auth": false
    },
    "web": {
        "enabled": true,
        "port": 8080
    }
}
```

---

## Examples

### Example 1: Character Animation Setup

```python
from llm.llm_integration import create_blender_assistant

assistant = create_blender_assistant(provider="claude")

# Complete character setup
assistant.execute("""
1. Create a humanoid rig named 'HeroRig', 1.8 meters tall
2. Create a sphere to represent the character body
3. Parent the sphere to the rig with automatic weights
4. Animate the rig walking forward over 60 frames
5. Add a camera following the character
""")
```

### Example 2: Product Visualization

```python
assistant.execute("""
Create a product showcase scene:
1. White cyclorama backdrop
2. Reflective marble floor
3. Three-point lighting setup
4. Camera at 45 degree angle
5. Product placeholder (black cube) at center
6. Render at 1920x1080
""")
```

### Example 3: Architectural Walkthrough

```python
assistant.execute("""
Create a simple room interior:
1. 5x4 meter room with 3 meter walls
2. Two windows on the front wall
3. Wooden floor material
4. Table and chair furniture
5. Ceiling light
6. Animate camera walking through the room
""")
```

---

## API Reference

### Advanced Tools API

| Method | Parameters | Description |
|--------|------------|-------------|
| `create_humanoid_rig` | name, height, location | Create full humanoid rig |
| `auto_weight_paint` | mesh_object, armature_object | Auto weight painting |
| `animate_location` | object_name, keyframes | Animate position |
| `animate_rotation` | object_name, keyframes | Animate rotation |
| `create_bouncing_ball_animation` | object_name, frames, bounces | Bouncing ball |
| `create_camera_animation` | camera_name, type, target | Camera animation |
| `batch_export` | directory, format, individual | Export multiple |
| `batch_import` | directory, format | Import multiple |
| `cleanup_unused_data` | materials, meshes, etc | Clean scene |
| `add_geometry_nodes_modifier` | object_name | Add GeoNodes |

### LLM API

```python
from llm.llm_integration import LLMManager, ClaudeProvider, GPTProvider

# Direct provider usage
claude = ClaudeProvider(api_key="...")
response = claude.chat(messages=[...], tools=[...])

# Manager with conversation
llm = LLMManager(provider="claude")
response = llm.chat("Create a sphere")
```

---

## Troubleshooting

### LLM Connection Issues

```
Error: API key not provided
```
**Solution:** Set environment variable or pass api_key parameter.

### Tool Execution Fails

```
Error: Object not found
```
**Solution:** Check object names are correct. Use `get_scene_info` to list objects.

### Web Interface Won't Connect

```
WebSocket connection failed
```
**Solution:** Ensure Blender WebSocket server is running first.

---

## Next Steps (Phase 3)

- [ ] Multi-user collaboration support
- [ ] Cloud deployment options
- [ ] Advanced AI-assisted modeling
- [ ] Voice control integration
- [ ] Plugin marketplace

---

## File Structure

```
blender-mcp/
├── server/
│   ├── mcp_server.py           # MCP stdio server
│   ├── websocket_server.py     # WebSocket server
│   ├── tools.py                # Basic tools
│   └── advanced/
│       └── tools_advanced.py   # Advanced tools (NEW)
├── llm/
│   ├── llm_integration.py      # LLM providers (NEW)
│   └── context_manager.py      # Context management (NEW)
├── prompts/
│   └── prompt_templates.py     # Template library (NEW)
├── web_interface/
│   ├── index.html              # Web UI (NEW)
│   └── server.py               # Web server (NEW)
├── addon/
│   └── __init__.py             # Blender addon
├── examples/
│   ├── basic_usage.py
│   ├── advanced.py
│   └── test_server.py
└── docs/
    ├── api.md
    ├── quickstart.md
    └── PHASE2.md               # This file (NEW)
```

---

**Phase 2 Complete!** 🎉

Ready for production use with advanced automation capabilities.
