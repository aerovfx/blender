# SPDX-FileCopyrightText: 2025 Blender MCP Project
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "MCP Server",
    "author": "Blender MCP Team",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > MCP Server",
    "description": "Enable MCP/WebSocket server for AI automation and remote control",
    "warning": "",
    "doc_url": "https://github.com/blender/blender-mcp",
    "category": "Interface",
}

import sys
import os
import threading
import json

# Add server directory to path
addon_dir = os.path.dirname(os.path.abspath(__file__))
server_dir = os.path.join(addon_dir, "..", "..", "server")
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

import bpy
from bpy.props import (
    StringProperty,
    IntProperty,
    BoolProperty,
    PointerProperty,
    EnumProperty,
)
from bpy.types import (
    Panel,
    Operator,
    PropertyGroup,
    AddonPreferences,
)


# ============================================================================
# Global Server State
# ============================================================================

_server_instance = None
_server_thread = None
_server_status = "stopped"  # stopped, starting, running, error
_server_error_message = ""


def get_server_status():
    """Get current server status."""
    global _server_status
    return _server_status


def set_server_status(status, error_msg=""):
    """Set server status."""
    global _server_status, _server_error_message
    _server_status = status
    _server_error_message = error_msg


# ============================================================================
# Property Group
# ============================================================================

class MCPServerProperties(PropertyGroup):
    """Properties for MCP Server configuration."""

    host: StringProperty(
        name="Host",
        description="Host address to bind the server",
        default="localhost",
    )

    port: IntProperty(
        name="Port",
        description="Port number for the server",
        default=8765,
        min=1024,
        max=65535,
    )

    transport: EnumProperty(
        name="Transport",
        description="Communication transport method",
        items=[
            ("websocket", "WebSocket", "WebSocket server for web clients"),
            ("stdio", "Stdio", "Standard I/O for MCP clients (Claude Desktop)"),
        ],
        default="websocket",
    )

    api_key: StringProperty(
        name="API Key",
        description="API key for authentication (leave empty for auto-generate)",
        default="",
        subtype='PASSWORD',
    )

    require_auth: BoolProperty(
        name="Require Authentication",
        description="Require clients to authenticate before using commands",
        default=False,
    )

    rate_limit: IntProperty(
        name="Rate Limit",
        description="Maximum requests per minute per client",
        default=100,
        min=1,
        max=10000,
    )

    is_running: BoolProperty(
        name="Running",
        description="Whether the server is currently running",
        default=False,
    )

    auto_start: BoolProperty(
        name="Auto Start",
        description="Start server automatically when Blender launches",
        default=False,
    )

    log_messages: BoolProperty(
        name="Log Messages",
        description="Log server messages to the console",
        default=True,
    )

    generated_api_key: StringProperty(
        name="Generated API Key",
        description="Auto-generated API key (shown when server starts)",
        default="",
    )


# ============================================================================
# Operators
# ============================================================================

class MCPStartServer(Operator):
    """Start the MCP Server"""
    bl_idname = "mcp.start_server"
    bl_label = "Start MCP Server"
    bl_description = "Start the MCP/WebSocket server for AI automation"
    bl_options = {'REGISTER'}

    _timer = None

    def modal(self, context, event):
        if event.type == 'TIMER':
            # Check server status
            status = get_server_status()
            props = context.scene.mcp_server

            if status == "running":
                props.is_running = True
                self.report({'INFO'}, "MCP Server is running")
                context.window_manager.event_timer_remove(self._timer)
                return {'FINISHED'}
            elif status == "error":
                props.is_running = False
                self.report({'ERROR'}, f"Server error: {_server_error_message}")
                context.window_manager.event_timer_remove(self._timer)
                return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        props = context.scene.mcp_server

        if props.is_running:
            self.report({'WARNING'}, "Server is already running")
            return {'CANCELLED'}

        # Import server module
        try:
            from websocket_server import (
                BlenderWebSocketServer,
                ServerConfig,
                start_server_thread,
            )
        except ImportError as e:
            self.report({'ERROR'}, f"Failed to import server module: {e}")
            return {'CANCELLED'}

        # Create configuration
        config = ServerConfig(
            host=props.host,
            port=props.port,
            api_key=props.api_key if props.api_key else None,
            require_auth=props.require_auth,
            rate_limit=props.rate_limit,
        )

        # Start server in background thread
        set_server_status("starting")

        try:
            global _server_instance, _server_thread
            _server_instance = BlenderWebSocketServer(config)

            def run_server():
                try:
                    set_server_status("running")
                    # Store generated API key
                    if props.api_key:
                        props.generated_api_key = props.api_key
                    else:
                        props.generated_api_key = _server_instance.security.get_api_key()
                    _server_instance.start()
                except Exception as e:
                    set_server_status("error", str(e))
                    props.is_running = False

            _server_thread = threading.Thread(target=run_server, daemon=True)
            _server_thread.start()

            # Start timer to check server status
            wm = context.window_manager
            self._timer = wm.event_timer_add(0.5, window=context.window)
            wm.modal_handler_add(self)

            return {'RUNNING_MODAL'}

        except Exception as e:
            set_server_status("error", str(e))
            props.is_running = False
            self.report({'ERROR'}, f"Failed to start server: {e}")
            return {'CANCELLED'}


class MCPStopServer(Operator):
    """Stop the MCP Server"""
    bl_idname = "mcp.stop_server"
    bl_label = "Stop MCP Server"
    bl_description = "Stop the MCP/WebSocket server"
    bl_options = {'REGISTER'}

    def execute(self, context):
        props = context.scene.mcp_server

        if not props.is_running:
            self.report({'WARNING'}, "Server is not running")
            return {'CANCELLED'}

        try:
            global _server_instance, _server_thread
            if _server_instance:
                _server_instance.stop()
                _server_instance = None
            _server_thread = None

            props.is_running = False
            set_server_status("stopped")

            self.report({'INFO'}, "MCP Server stopped")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Error stopping server: {e}")
            return {'CANCELLED'}


class MCPCopyAPIKey(Operator):
    """Copy API key to clipboard"""
    bl_idname = "mcp.copy_api_key"
    bl_label = "Copy API Key"
    bl_description = "Copy the API key to clipboard"
    bl_options = {'REGISTER'}

    def execute(self, context):
        props = context.scene.mcp_server

        if props.generated_api_key:
            context.window_manager.clipboard = props.generated_api_key
            self.report({'INFO'}, "API key copied to clipboard")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No API key available")
            return {'CANCELLED'}


class MCPTestConnection(Operator):
    """Test connection to the server"""
    bl_idname = "mcp.test_connection"
    bl_label = "Test Connection"
    bl_description = "Test the connection to the MCP server"
    bl_options = {'REGISTER'}

    def execute(self, context):
        props = context.scene.mcp_server

        try:
            import websocket
            import json

            # Create a test connection
            ws = websocket.create_connection(
                f"ws://{props.host}:{props.port}",
                timeout=5
            )

            # Send ping
            ws.send(json.dumps({"type": "ping", "id": 1}))
            response = json.loads(ws.recv())
            ws.close()

            if response.get("type") == "pong":
                self.report({'INFO'}, "Connection successful!")
                return {'FINISHED'}
            else:
                self.report({'WARNING'}, f"Unexpected response: {response}")
                return {'CANCELLED'}

        except Exception as e:
            self.report({'ERROR'}, f"Connection failed: {e}")
            return {'CANCELLED'}


# ============================================================================
# UI Panel
# ============================================================================

class MCPPanel(Panel):
    """MCP Server Panel in View3D"""
    bl_label = "MCP Server"
    bl_idname = "VIEW3D_PT_mcp_server"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MCP Server"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.mcp_server

        # Status indicator
        status = get_server_status()
        status_row = layout.row()
        status_row.alignment = 'CENTER'

        if status == "running":
            status_row.label(text="● Server Running", icon='CHECKMARK')
            status_row.enabled = True
        elif status == "starting":
            status_row.label(text="● Starting...", icon='TEMP')
        elif status == "error":
            status_row.label(text="● Error", icon='ERROR')
        else:
            status_row.label(text="● Server Stopped", icon='X')

        # Server configuration
        box = layout.box()
        box.label(text="Configuration", icon='SETTINGS')

        split = box.split(factor=0.35)
        split.label(text="Transport:")
        split.prop(props, "transport", text="")

        split = box.split(factor=0.35)
        split.label(text="Host:")
        split.prop(props, "host", text="")

        split = box.split(factor=0.35)
        split.label(text="Port:")
        split.prop(props, "port", text="")

        # Security settings
        box = layout.box()
        box.label(text="Security", icon='LOCKED')

        split = box.split(factor=0.35)
        split.label(text="API Key:")
        row = split.row()
        row.prop(props, "api_key", text="")
        row.enabled = not props.is_running

        split = box.split(factor=0.35)
        split.label(text="Require Auth:")
        row = split.row()
        row.prop(props, "require_auth", text="")
        row.enabled = not props.is_running

        split = box.split(factor=0.35)
        split.label(text="Rate Limit:")
        row = split.row()
        row.prop(props, "rate_limit", text="")
        row.enabled = not props.is_running
        row.label(text="/min")

        # Generated API key display
        if props.generated_api_key:
            api_box = layout.box()
            api_box.label(text="Generated API Key:", icon='KEYINGSET')
            api_row = api_box.row(align=True)
            api_row.prop(props, "generated_api_key", text="")
            api_row.operator("mcp.copy_api_key", text="", icon='COPYDOWN')

        # Start/Stop buttons
        layout.separator()

        row = layout.row(align=True)
        row.scale_y = 1.5

        if props.is_running or status == "running":
            row.operator("mcp.stop_server", text="Stop Server", icon='PAUSE')
        else:
            row.operator("mcp.start_server", text="Start Server", icon='PLAY')

        # Test connection button
        if props.is_running or status == "running":
            layout.separator()
            layout.operator("mcp.test_connection", icon='NETWORK_DRIVE')

        # Connection info
        if props.is_running or status == "running":
            layout.separator()
            box = layout.box()
            box.label(text="Connection Info", icon='INFO')
            box.label(text=f"ws://{props.host}:{props.port}")

            # MCP config for Claude Desktop
            box.separator()
            box.label(text="Claude Desktop Config:")
            config_text = (
                f'"command": "blender",\n'
                f'"args": ["--background", "--python", '
                f'"/path/to/mcp_server.py"]'
            )
            config_box = box.box()
            for line in config_text.split('\n'):
                config_box.label(text=line)


# ============================================================================
# Addon Preferences
# ============================================================================

class MCPAddonPreferences(AddonPreferences):
    """MCP Server Addon Preferences"""
    bl_idname = __name__

    auto_start: BoolProperty(
        name="Auto Start Server",
        description="Start MCP server automatically when Blender launches",
        default=False,
    )

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="General Settings", icon='PREFERENCES')
        box.prop(self, "auto_start")

        box = layout.box()
        box.label(text="About", icon='INFO')
        box.label(text="MCP Server for Blender v1.0.0")
        box.label(text="Enable AI automation and remote control")
        box.operator(
            "wm.url_open",
            text="Documentation",
            icon='URL',
        ).url = "https://github.com/blender/blender-mcp"


# ============================================================================
# Registration
# ============================================================================

classes = (
    MCPServerProperties,
    MCPStartServer,
    MCPStopServer,
    MCPCopyAPIKey,
    MCPTestConnection,
    MCPPanel,
    MCPAddonPreferences,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.mcp_server = PointerProperty(type=MCPServerProperties)

    # Auto-start if enabled
    prefs = bpy.context.preferences.addons.get(__name__)
    if prefs and prefs.preferences.auto_start:
        # Delay start to allow Blender to fully initialize
        def auto_start():
            bpy.ops.mcp.start_server()
            return None

        bpy.app.timers.register(auto_start, first_interval=2.0)


def unregister():
    # Stop server if running
    try:
        bpy.ops.mcp.stop_server()
    except:
        pass

    del bpy.types.Scene.mcp_server

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
