# Quick Start Guide

## Installation

### 1. Install Dependencies

```bash
cd /Users/pixibox/blender/blender-mcp
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
# Check Python packages
python -c "import mcp; import websockets; print('OK')"
```

---

## Usage Methods

### Method 1: WebSocket Server (Recommended for Development)

**Start the server:**

```bash
# Option A: From command line
blender --background --python /Users/pixibox/blender/blender-mcp/server/websocket_server.py

# Option B: With custom settings
blender --background --python /Users/pixibox/blender/blender-mcp/server/websocket_server.py -- \
    --host 0.0.0.0 \
    --port 8765 \
    --api-key my-secret-key \
    --require-auth \
    --rate-limit 200
```

**Test the connection:**

```bash
python /Users/pixibox/blender/blender-mcp/examples/test_server.py
```

**Run examples:**

```bash
# Basic examples
python /Users/pixibox/blender/blender-mcp/examples/basic_usage.py

# Advanced examples
python /Users/pixibox/blender/blender-mcp/examples/advanced.py
```

---

### Method 2: Blender Addon (Recommended for Interactive Use)

**Install the addon:**

```bash
# Copy to Blender addons directory
# macOS
cp -r /Users/pixibox/blender/blender-mcp/addon \
      ~/Library/Application\ Support/Blender/4.0/scripts/addons/blender_mcp

# Linux
cp -r /Users/pixibox/blender/blender-mcp/addon \
      ~/.config/blender/4.0/scripts/addons/blender_mcp

# Windows
# Copy to: C:\Users\<YourName>\AppData\Roaming\Blender Foundation\Blender\4.0\scripts\addons\
```

**Enable the addon:**

1. Open Blender
2. Go to `Edit > Preferences > Add-ons`
3. Search for "MCP"
4. Check the box to enable

**Use the addon:**

1. Open the 3D Viewport
2. Press `N` to open the sidebar
3. Click on the "MCP Server" tab
4. Configure settings (host, port, API key)
5. Click "Start Server"

---

### Method 3: MCP Stdio (For Claude Desktop Integration)

**Configure Claude Desktop:**

Create/edit `~/.config/claude/claude_desktop_config.json`:

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

**Restart Claude Desktop** and start chatting!

**Example prompts:**

```
Create a cityscape with 10 buildings

Add a red sphere at position (5, 0, 0)

Create a camera looking at the origin

Export all objects as FBX files
```

---

## Testing

### Run All Tests

```bash
python /Users/pixibox/blender/blender-mcp/examples/test_server.py
```

### Run Specific Tests

```bash
# Test connection only
python /Users/pixibox/blender/blender-mcp/examples/test_server.py --test connection

# Test object creation
python /Users/pixibox/blender/blender-mcp/examples/test_server.py --test create
```

---

## Troubleshooting

### Connection Refused

**Problem:** `ConnectionRefusedError: [Errno 111] Connection refused`

**Solution:**
1. Make sure the server is running
2. Check the host and port are correct
3. Check firewall settings

### Module Not Found

**Problem:** `ModuleNotFoundError: No module named 'mcp'`

**Solution:**
```bash
pip install -r requirements.txt
```

### Blender Python Version

**Problem:** Packages installed but not found in Blender

**Solution:** Blender uses its own Python installation. Install packages to Blender's Python:

```bash
# Find Blender's Python
/Applications/Blender.app/Contents/Resources/4.0/python/bin/python3.11 -m pip install mcp websockets

# Or set PYTHONPATH
export PYTHONPATH="/path/to/blender-mcp/server:$PYTHONPATH"
```

### Server Won't Start

**Problem:** Server fails to start

**Solution:**
1. Check Blender version (requires 4.0+)
2. Run with verbose output:
   ```bash
   blender --background --python websocket_server.py -- --port 8765
   ```
3. Check for port conflicts:
   ```bash
   lsof -i :8765
   ```

---

## Next Steps

1. **Read the API Documentation:** `docs/api.md`
2. **Try the Examples:** `examples/basic_usage.py`, `examples/advanced.py`
3. **Customize:** Modify `server/tools.py` to add custom tools
4. **Integrate:** Connect to your favorite LLM or build a web interface

---

## Quick Reference

### Start Commands

```bash
# WebSocket server
blender --background --python server/websocket_server.py

# MCP server (for Claude)
blender --background --python server/mcp_server.py

# With custom port
blender --background --python server/websocket_server.py -- --port 9000

# With authentication
blender --background --python server/websocket_server.py -- --api-key secret --require-auth
```

### Test Commands

```bash
# Run all tests
python examples/test_server.py

# Run basic examples
python examples/basic_usage.py

# Run advanced examples
python examples/advanced.py
```

### WebSocket URL

```
ws://localhost:8765
```

### Default API Key

If not specified, an API key is auto-generated and printed to console.
