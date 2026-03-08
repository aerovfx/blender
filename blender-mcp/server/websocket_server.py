#!/usr/bin/env python3
"""
Blender WebSocket Server - Real-time bidirectional communication.

This server allows remote clients to control Blender via WebSocket
using a JSON-RPC-like protocol.

Usage:
    blender --background --python websocket_server.py -- --port 8765
"""

import sys
import os

# Add the server directory to path
server_dir = os.path.dirname(os.path.abspath(__file__))
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

import asyncio
import json
from typing import Any, Optional, Set
from dataclasses import dataclass

# Try to import websockets, provide fallback message
try:
    import websockets
    from websockets.server import WebSocketServerProtocol
except ImportError:
    print("Error: websockets package not installed.")
    print("Install with: pip install websockets")
    sys.exit(1)

# Import Blender tools and security
from tools import BlenderTools
from security import SecurityManager, RateLimiter


@dataclass
class ServerConfig:
    """Server configuration."""
    host: str = "localhost"
    port: int = 8765
    api_key: Optional[str] = None
    require_auth: bool = False
    rate_limit: int = 100  # requests per minute
    allowed_commands: Optional[Set[str]] = None


class BlenderWebSocketServer:
    """WebSocket server for Blender control."""

    def __init__(self, config: Optional[ServerConfig] = None):
        self.config = config or ServerConfig()
        self.tools = BlenderTools()
        self.security = SecurityManager(
            api_key=self.config.api_key,
            rate_limit=self.config.rate_limit
        )
        self.clients: Set[WebSocketServerProtocol] = set()
        self._server = None
        self._running = False

    async def handler(self, websocket: WebSocketServerProtocol) -> None:
        """Handle WebSocket connection."""
        # Register client
        self.clients.add(websocket)
        client_addr = websocket.remote_address
        print(f"[+] Client connected: {client_addr}")

        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "welcome",
                "message": "Connected to Blender MCP WebSocket Server",
                "version": "1.0.0"
            }))

            # Process messages
            async for message in websocket:
                try:
                    response = await self.process_message(websocket, message)
                    await websocket.send(json.dumps(response))
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": "Invalid JSON"
                    }))
                except Exception as e:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": str(e)
                    }))

        except websockets.exceptions.ConnectionClosed:
            print(f"[-] Client disconnected: {client_addr}")
        finally:
            self.clients.remove(websocket)

    async def process_message(
        self,
        websocket: WebSocketServerProtocol,
        message: str
    ) -> dict[str, Any]:
        """Process incoming message and return response."""
        data = json.loads(message)

        # Extract message fields
        msg_type = data.get("type", "request")
        msg_id = data.get("id")
        method = data.get("method")
        params = data.get("params", {})

        # Handle different message types
        if msg_type == "ping":
            return {"type": "pong", "id": msg_id}

        if msg_type == "auth":
            return await self.handle_auth(websocket, params)

        if msg_type == "request" and method:
            return await self.handle_request(websocket, msg_id, method, params)

        return {
            "type": "error",
            "id": msg_id,
            "error": f"Unknown message type: {msg_type}"
        }

    async def handle_auth(
        self,
        websocket: WebSocketServerProtocol,
        params: dict
    ) -> dict:
        """Handle authentication request."""
        api_key = params.get("api_key")

        if self.security.authenticate(api_key):
            return {
                "type": "auth_success",
                "message": "Authentication successful"
            }
        else:
            return {
                "type": "auth_failed",
                "error": "Invalid API key"
            }

    async def handle_request(
        self,
        websocket: WebSocketServerProtocol,
        msg_id: Any,
        method: str,
        params: dict
    ) -> dict:
        """Handle tool request."""
        # Check authentication if required
        if self.config.require_auth:
            if not self.security.is_authenticated(websocket):
                return {
                    "type": "error",
                    "id": msg_id,
                    "error": "Authentication required. Send auth request first."
                }

        # Rate limiting
        if not self.security.check_rate_limit():
            return {
                "type": "error",
                "id": msg_id,
                "error": "Rate limit exceeded"
            }

        # Command whitelist check
        if self.config.allowed_commands:
            if method not in self.config.allowed_commands:
                return {
                    "type": "error",
                    "id": msg_id,
                    "error": f"Command not allowed: {method}"
                }

        # Execute the tool
        try:
            result = await self.execute_tool(method, params)
            return {
                "type": "response",
                "id": msg_id,
                "result": result
            }
        except Exception as e:
            return {
                "type": "error",
                "id": msg_id,
                "error": str(e)
            }

    async def execute_tool(
        self,
        method: str,
        params: dict
    ) -> dict:
        """Execute a Blender tool."""
        # Map of available tools
        tools = {
            "create_object": self.tools.create_object,
            "delete_object": self.tools.delete_object,
            "get_scene_info": self.tools.get_scene_info,
            "get_object_info": self.tools.get_object_info,
            "modify_object": self.tools.modify_object,
            "set_material": self.tools.set_material,
            "create_camera": self.tools.create_camera,
            "create_light": self.tools.create_light,
            "render_scene": self.tools.render_scene,
            "export_file": self.tools.export_file,
            "clear_scene": self.tools.clear_scene,
        }

        if method not in tools:
            available = list(tools.keys())
            raise ValueError(f"Unknown method: {method}. Available: {available}")

        # Execute the tool
        return tools[method](**params)

    async def broadcast(self, message: dict) -> None:
        """Broadcast message to all connected clients."""
        if self.clients:
            data = json.dumps(message)
            await asyncio.gather(
                *[client.send(data) for client in self.clients],
                return_exceptions=True
            )

    def start(self) -> None:
        """Start the WebSocket server (blocking)."""
        self._running = True

        start_server = websockets.serve(
            self.handler,
            self.config.host,
            self.config.port
        )

        print(f"=" * 50)
        print(f"Blender MCP WebSocket Server")
        print(f"=" * 50)
        print(f"Host: {self.config.host}")
        print(f"Port: {self.config.port}")
        print(f"Authentication: {'Required' if self.config.require_auth else 'Optional'}")
        if self.config.allowed_commands:
            print(f"Allowed commands: {self.config.allowed_commands}")
        print(f"=" * 50)
        print(f"Connect: ws://{self.config.host}:{self.config.port}")
        print(f"Press Ctrl+C to stop")
        print(f"=" * 50)

        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    def stop(self) -> None:
        """Stop the server."""
        self._running = False
        print("Server stopping...")


def parse_args() -> ServerConfig:
    """Parse command line arguments."""
    import argparse

    parser = argparse.ArgumentParser(description="Blender MCP WebSocket Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on")
    parser.add_argument("--api-key", help="API key for authentication")
    parser.add_argument("--require-auth", action="store_true", help="Require authentication")
    parser.add_argument("--rate-limit", type=int, default=100, help="Rate limit (requests/min)")
    parser.add_argument("--allowed-commands", nargs="+", help="Allowed commands (whitelist)")

    args = parser.parse_args()

    return ServerConfig(
        host=args.host,
        port=args.port,
        api_key=args.api_key,
        require_auth=args.require_auth,
        rate_limit=args.rate_limit,
        allowed_commands=set(args.allowed_commands) if args.allowed_commands else None
    )


# Global server instance for addon communication
_server_instance: Optional[BlenderWebSocketServer] = None


def get_server() -> Optional[BlenderWebSocketServer]:
    """Get the global server instance."""
    return _server_instance


def start_server_thread(config: Optional[ServerConfig] = None) -> None:
    """Start server in a background thread (for addon use)."""
    import threading

    global _server_instance
    _server_instance = BlenderWebSocketServer(config)

    thread = threading.Thread(target=_server_instance.start, daemon=True)
    thread.start()

    return _server_instance


def stop_server() -> None:
    """Stop the global server instance."""
    global _server_instance
    if _server_instance:
        _server_instance.stop()
        _server_instance = None


if __name__ == "__main__":
    # Parse arguments
    config = parse_args()

    # Create and start server
    server = BlenderWebSocketServer(config)
    server.start()
