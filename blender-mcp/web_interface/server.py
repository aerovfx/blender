#!/usr/bin/env python3
"""
Web Server for Blender MCP Bot Control Interface.

Provides a web-based UI for controlling Blender through the MCP server.
"""

import asyncio
import json
import websockets
from aiohttp import web
from typing import Optional, Set
import os


class BlenderMCPWebServer:
    """Web server for Blender MCP control interface."""

    def __init__(self, host: str = "localhost", port: int = 8080, 
                 blender_ws_url: str = "ws://localhost:8765"):
        self.host = host
        self.port = port
        self.blender_ws_url = blender_ws_url
        self.app = web.Application()
        self.blender_ws: Optional[websockets.WebSocketClientProtocol] = None
        self.websocket_clients: Set[web.WebSocketResponse] = set()
        
        self._setup_routes()

    def _setup_routes(self):
        """Setup web routes."""
        self.app.router.add_get("/", self.handle_index)
        self.app.router.add_get("/static/{filename}", self.handle_static)
        self.app.router.add_get("/ws", self.handle_websocket)
        self.app.router.add_post("/api/command", self.handle_command)
        self.app.router.add_get("/api/scene", self.handle_scene_info)
        self.app.router.add_get("/api/templates", self.handle_templates)

    async def handle_index(self, request: web.Request) -> web.Response:
        """Serve the main HTML page."""
        file_path = os.path.join(os.path.dirname(__file__), "index.html")
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return web.Response(text=f.read(), content_type='text/html')
        else:
            return web.Response(text="Index file not found", status=404)

    async def handle_static(self, request: web.Request) -> web.Response:
        """Serve static files."""
        filename = request.match_info['filename']
        file_path = os.path.join(os.path.dirname(__file__), filename)
        
        if os.path.exists(file_path):
            return web.FileResponse(file_path)
        else:
            return web.Response(text="File not found", status=404)

    async def handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connections from web clients."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.websocket_clients.add(ws)
        print(f"[+] Web client connected. Total: {len(self.websocket_clients)}")

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    await self.handle_web_message(ws, json.loads(msg.data))
                elif msg.type == web.WSMsgType.ERROR:
                    print(f"WebSocket error: {ws.exception()}")
        finally:
            self.websocket_clients.remove(ws)
            print(f"[-] Web client disconnected. Total: {len(self.websocket_clients)}")

        return ws

    async def handle_web_message(self, ws: web.WebSocketResponse, data: dict):
        """Handle message from web client."""
        msg_type = data.get("type")
        
        if msg_type == "command":
            await self.forward_to_blender(data)
        elif msg_type == "connect_blender":
            await self.connect_to_blender()

    async def connect_to_blender(self):
        """Connect to Blender WebSocket server."""
        try:
            self.blender_ws = await websockets.connect(self.blender_ws_url)
            print(f"Connected to Blender at {self.blender_ws_url}")
            
            # Start listening for Blender messages
            asyncio.create_task(self.listen_to_blender())
        except Exception as e:
            print(f"Failed to connect to Blender: {e}")

    async def listen_to_blender(self):
        """Listen for messages from Blender."""
        try:
            async for message in self.blender_ws:
                await self.broadcast_to_web(json.loads(message))
        except websockets.exceptions.ConnectionClosed:
            print("Disconnected from Blender")
            self.blender_ws = None

    async def forward_to_blender(self, data: dict):
        """Forward command to Blender."""
        if not self.blender_ws:
            await self.connect_to_blender()
        
        if self.blender_ws:
            # Convert web format to Blender MCP format
            blender_msg = {
                "type": "request",
                "id": data.get("id", 1),
                "method": data.get("method"),
                "params": data.get("params", {})
            }
            await self.blender_ws.send(json.dumps(blender_msg))

    async def broadcast_to_web(self, data: dict):
        """Broadcast message to all web clients."""
        if self.websocket_clients:
            await asyncio.gather(
                *[client.send_json(data) for client in self.websocket_clients],
                return_exceptions=True
            )

    async def handle_command(self, request: web.Request) -> web.Response:
        """Handle HTTP API command."""
        try:
            data = await request.json()
            
            if not self.blender_ws:
                return web.json_response({
                    "success": False,
                    "error": "Not connected to Blender"
                }, status=503)

            # Send to Blender
            msg = {
                "type": "request",
                "id": 1,
                "method": data.get("method"),
                "params": data.get("params", {})
            }
            await self.blender_ws.send(json.dumps(msg))

            # Wait for response
            response = await asyncio.wait_for(
                self.blender_ws.recv(),
                timeout=10.0
            )

            return web.json_response(json.loads(response))

        except asyncio.TimeoutError:
            return web.json_response({
                "success": False,
                "error": "Timeout waiting for Blender response"
            }, status=504)
        except Exception as e:
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def handle_scene_info(self, request: web.Request) -> web.Response:
        """Get scene information."""
        return await self.handle_command(request)

    async def handle_templates(self, request: web.Request) -> web.Response:
        """Get available prompt templates."""
        templates = [
            {"id": "simple_scene", "name": "Simple Scene"},
            {"id": "product_showcase", "name": "Product Showcase"},
            {"id": "bouncing_ball", "name": "Bouncing Ball"},
            {"id": "architectural_interior", "name="Room Interior"},
        ]
        return web.json_response({"templates": templates})

    async def start(self):
        """Start the web server."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        print(f"=" * 50)
        print(f"Blender MCP Web Interface")
        print(f"=" * 50)
        print(f"Web UI: http://{self.host}:{self.port}")
        print(f"Blender WS: {self.blender_ws_url}")
        print(f"=" * 50)

    def start_blocking(self):
        """Start the web server (blocking)."""
        asyncio.get_event_loop().run_until_complete(self.start())
        asyncio.get_event_loop().run_forever()


def run_web_server(host: str = "localhost", port: int = 8080,
                   blender_ws: str = "ws://localhost:8765"):
    """Run the web server."""
    server = BlenderMCPWebServer(host=host, port=port, blender_ws_url=blender_ws)
    server.start_blocking()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Blender MCP Web Server")
    parser.add_argument("--host", default="localhost", help="Web server host")
    parser.add_argument("--port", type=int, default=8080, help="Web server port")
    parser.add_argument("--blender-ws", default="ws://localhost:8765",
                       help="Blender WebSocket URL")
    
    args = parser.parse_args()
    run_web_server(args.host, args.port, args.blender_ws)
