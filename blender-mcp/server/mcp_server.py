#!/usr/bin/env python3
"""
Blender MCP Server - Main entry point for stdio transport.

This script is designed to run inside Blender and communicate via stdio
with MCP clients (Claude Desktop, etc.).

Usage:
    blender --background --python mcp_server.py
"""

import sys
import os

# Add the server directory to path
server_dir = os.path.dirname(os.path.abspath(__file__))
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server

# Import Blender tools
from tools import BlenderTools


def create_server() -> Server:
    """Create and configure the MCP server."""
    server = Server("blender")
    tools = BlenderTools()

    @server.list_tools()
    async def list_tools() -> list[dict[str, Any]]:
        """Return list of available tools."""
        return [
            {
                "name": "create_object",
                "description": "Create a 3D primitive object (cube, sphere, cylinder, cone, torus, plane, light, camera)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["cube", "sphere", "cylinder", "cone", "torus", "plane", "light", "camera"],
                            "description": "Type of object to create"
                        },
                        "location": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 3,
                            "maxItems": 3,
                            "description": "Location (x, y, z) in 3D space"
                        },
                        "rotation": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 3,
                            "maxItems": 3,
                            "description": "Rotation (x, y, z) in Euler angles"
                        },
                        "scale": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 3,
                            "maxItems": 3,
                            "description": "Scale (x, y, z)"
                        },
                        "name": {
                            "type": "string",
                            "description": "Name for the new object"
                        },
                        "radius": {
                            "type": "number",
                            "description": "Radius for spheres, cylinders, torus"
                        },
                        "depth": {
                            "type": "number",
                            "description": "Depth/height for cylinders, cones"
                        },
                        "energy": {
                            "type": "number",
                            "description": "Light energy (for light type)"
                        },
                        "color": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 3,
                            "maxItems": 3,
                            "description": "Color (r, g, b) for lights"
                        }
                    },
                    "required": ["type"]
                }
            },
            {
                "name": "delete_object",
                "description": "Delete an object from the scene",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the object to delete"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "get_scene_info",
                "description": "Get information about the current scene including all objects",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_object_info",
                "description": "Get detailed information about a specific object",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the object"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "modify_object",
                "description": "Modify an object's transform (location, rotation, scale)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the object to modify"
                        },
                        "location": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 3,
                            "maxItems": 3,
                            "description": "New location (x, y, z)"
                        },
                        "rotation": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 3,
                            "maxItems": 3,
                            "description": "New rotation (x, y, z) in Euler angles"
                        },
                        "scale": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 3,
                            "maxItems": 3,
                            "description": "New scale (x, y, z)"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "set_material",
                "description": "Create or apply a material to an object",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "object_name": {
                            "type": "string",
                            "description": "Name of the object"
                        },
                        "material_name": {
                            "type": "string",
                            "description": "Name of the material (creates if not exists)"
                        },
                        "color": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 3,
                            "maxItems": 4,
                            "description": "Base color (r, g, b, [a])"
                        },
                        "metallic": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "description": "Metallic value (0-1)"
                        },
                        "roughness": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "description": "Roughness value (0-1)"
                        }
                    },
                    "required": ["object_name", "material_name"]
                }
            },
            {
                "name": "create_camera",
                "description": "Add a camera to the scene",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 3,
                            "maxItems": 3,
                            "description": "Camera location (x, y, z)"
                        },
                        "rotation": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 3,
                            "maxItems": 3,
                            "description": "Camera rotation (x, y, z) in Euler angles"
                        },
                        "name": {
                            "type": "string",
                            "description": "Camera name"
                        },
                        "focal_length": {
                            "type": "number",
                            "description": "Focal length in mm"
                        }
                    }
                }
            },
            {
                "name": "create_light",
                "description": "Add a light source to the scene",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["POINT", "SUN", "SPOT", "AREA"],
                            "description": "Light type"
                        },
                        "location": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 3,
                            "maxItems": 3,
                            "description": "Light location (x, y, z)"
                        },
                        "energy": {
                            "type": "number",
                            "description": "Light energy"
                        },
                        "color": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 3,
                            "maxItems": 3,
                            "description": "Light color (r, g, b)"
                        },
                        "name": {
                            "type": "string",
                            "description": "Light name"
                        }
                    },
                    "required": ["type"]
                }
            },
            {
                "name": "render_scene",
                "description": "Render the current scene to an image file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "Output file path"
                        },
                        "resolution_x": {
                            "type": "integer",
                            "description": "Render width in pixels"
                        },
                        "resolution_y": {
                            "type": "integer",
                            "description": "Render height in pixels"
                        },
                        "samples": {
                            "type": "integer",
                            "description": "Render samples"
                        }
                    }
                }
            },
            {
                "name": "export_file",
                "description": "Export the scene or selected objects to a file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "Output file path"
                        },
                        "format": {
                            "type": "string",
                            "enum": ["FBX", "OBJ", "GLTF", "STL", "PLY"],
                            "description": "Export format"
                        },
                        "use_selection": {
                            "type": "boolean",
                            "description": "Export only selected objects"
                        }
                    },
                    "required": ["filepath", "format"]
                }
            },
            {
                "name": "clear_scene",
                "description": "Remove all objects from the scene (DANGEROUS - requires confirmation)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "confirm": {
                            "type": "boolean",
                            "description": "Must be true to confirm deletion"
                        }
                    },
                    "required": ["confirm"]
                }
            }
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[dict[str, Any]]:
        """Execute a tool and return results."""
        try:
            if name == "create_object":
                result = tools.create_object(**arguments)
            elif name == "delete_object":
                result = tools.delete_object(**arguments)
            elif name == "get_scene_info":
                result = tools.get_scene_info()
            elif name == "get_object_info":
                result = tools.get_object_info(**arguments)
            elif name == "modify_object":
                result = tools.modify_object(**arguments)
            elif name == "set_material":
                result = tools.set_material(**arguments)
            elif name == "create_camera":
                result = tools.create_camera(**arguments)
            elif name == "create_light":
                result = tools.create_light(**arguments)
            elif name == "render_scene":
                result = tools.render_scene(**arguments)
            elif name == "export_file":
                result = tools.export_file(**arguments)
            elif name == "clear_scene":
                result = tools.clear_scene(**arguments)
            else:
                return [{
                    "type": "text",
                    "text": f"Error: Unknown tool '{name}'"
                }]

            return [{
                "type": "text",
                "text": json.dumps(result, indent=2, default=str)
            }]

        except Exception as e:
            return [{
                "type": "text",
                "text": f"Error executing {name}: {str(e)}"
            }]

    return server


async def main():
    """Main entry point."""
    server = create_server()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
