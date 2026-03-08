#!/usr/bin/env python3
"""
Basic usage examples for Blender MCP Server.

These examples demonstrate common operations using the WebSocket interface.
"""

import json
import websocket
import time


class BlenderMCPClient:
    """Simple client for Blender MCP WebSocket server."""

    def __init__(self, host="localhost", port=8765, timeout=5):
        self.url = f"ws://{host}:{port}"
        self.timeout = timeout
        self.ws = None
        self._id = 0

    def connect(self):
        """Connect to the server."""
        self.ws = websocket.create_connection(self.url, timeout=self.timeout)
        # Read welcome message
        welcome = json.loads(self.ws.recv())
        print(f"Connected: {welcome}")
        return welcome

    def disconnect(self):
        """Disconnect from the server."""
        if self.ws:
            self.ws.close()

    def _next_id(self):
        self._id += 1
        return self._id

    def call(self, method, **params):
        """Call a tool method and return result."""
        request = {
            "type": "request",
            "id": self._next_id(),
            "method": method,
            "params": params
        }
        self.ws.send(json.dumps(request))
        response = json.loads(self.ws.recv())
        
        if response.get("type") == "error":
            raise Exception(response.get("error", "Unknown error"))
        
        return response.get("result")

    def ping(self):
        """Test connection."""
        request = {"type": "ping", "id": self._next_id()}
        self.ws.send(json.dumps(request))
        response = json.loads(self.ws.recv())
        return response.get("type") == "pong"


# ============================================================================
# Example 1: Create Basic Objects
# ============================================================================

def example_create_objects():
    """Create various 3D primitives."""
    print("\n" + "="*50)
    print("Example 1: Create Basic Objects")
    print("="*50)

    client = BlenderMCPClient()
    client.connect()

    try:
        # Create a cube at origin
        result = client.call("create_object", type="cube", location=[0, 0, 0], name="BaseCube")
        print(f"Created cube: {result}")

        # Create a sphere
        result = client.call("create_object", type="sphere", location=[2, 0, 0], radius=0.5, name="Sphere1")
        print(f"Created sphere: {result}")

        # Create a cylinder
        result = client.call("create_object", type="cylinder", location=[-2, 0, 0], radius=0.3, depth=2, name="Cylinder1")
        print(f"Created cylinder: {result}")

        # Create a cone
        result = client.call("create_object", type="cone", location=[0, 2, 0], radius=0.5, depth=1.5, name="Cone1")
        print(f"Created cone: {result}")

        # Create a torus
        result = client.call("create_object", type="torus", location=[0, -2, 0], radius=0.5, name="Torus1")
        print(f"Created torus: {result}")

    finally:
        client.disconnect()


# ============================================================================
# Example 2: Scene Information
# ============================================================================

def example_scene_info():
    """Get scene information."""
    print("\n" + "="*50)
    print("Example 2: Scene Information")
    print("="*50)

    client = BlenderMCPClient()
    client.connect()

    try:
        # Get scene info
        info = client.call("get_scene_info")
        print(f"Scene: {info['scene_name']}")
        print(f"Frame: {info['frame_current']}")
        print(f"Objects: {info['object_count']}")
        print(f"Render Engine: {info['render_engine']}")

        # List all objects
        print("\nObjects in scene:")
        for obj in info['objects']:
            print(f"  - {obj['name']} ({obj['type']}) at {obj['location']}")

    finally:
        client.disconnect()


# ============================================================================
# Example 3: Modify Objects
# ============================================================================

def example_modify_objects():
    """Modify object transforms."""
    print("\n" + "="*50)
    print("Example 3: Modify Objects")
    print("="*50)

    client = BlenderMCPClient()
    client.connect()

    try:
        # Create an object first
        result = client.call("create_object", type="cube", name="ModifiableCube")
        print(f"Created: {result}")

        # Move it
        result = client.call("modify_object", name="ModifiableCube", location=[5, 0, 0])
        print(f"Moved to [5, 0, 0]: {result}")

        # Rotate it
        result = client.call("modify_object", name="ModifiableCube", rotation=[0, 0, 45])
        print(f"Rotated 45° on Z: {result}")

        # Scale it
        result = client.call("modify_object", name="ModifiableCube", scale=[2, 2, 2])
        print(f"Scaled 2x: {result}")

        # Get detailed info
        info = client.call("get_object_info", name="ModifiableCube")
        print(f"Object info: {json.dumps(info, indent=2)}")

    finally:
        client.disconnect()


# ============================================================================
# Example 4: Materials
# ============================================================================

def example_materials():
    """Create and apply materials."""
    print("\n" + "="*50)
    print("Example 4: Materials")
    print("="*50)

    client = BlenderMCPClient()
    client.connect()

    try:
        # Create objects
        client.call("create_object", type="sphere", location=[-1, 0, 0], name="RedSphere")
        client.call("create_object", type="sphere", location=[1, 0, 0], name="BlueSphere")

        # Apply red material
        result = client.call("set_material", 
                           object_name="RedSphere", 
                           material_name="RedMaterial",
                           color=[1, 0, 0],
                           roughness=0.5)
        print(f"Red material: {result}")

        # Apply blue metallic material
        result = client.call("set_material", 
                           object_name="BlueSphere", 
                           material_name="BlueMetal",
                           color=[0, 0, 1],
                           metallic=0.9,
                           roughness=0.1)
        print(f"Blue metal material: {result}")

    finally:
        client.disconnect()


# ============================================================================
# Example 5: Lights and Cameras
# ============================================================================

def example_lights_cameras():
    """Create lights and cameras."""
    print("\n" + "="*50)
    print("Example 5: Lights and Cameras")
    print("="*50)

    client = BlenderMCPClient()
    client.connect()

    try:
        # Create a camera
        result = client.call("create_camera", 
                           location=[10, 10, 10], 
                           rotation=[45, 0, 45],
                           name="MainCamera",
                           focal_length=50)
        print(f"Created camera: {result}")

        # Create a sun light
        result = client.call("create_light", 
                           type="SUN",
                           location=[5, 5, 10],
                           energy=2.0,
                           name="Sun")
        print(f"Created sun: {result}")

        # Create a point light
        result = client.call("create_light", 
                           type="POINT",
                           location=[0, 0, 5],
                           energy=100,
                           color=[1, 0.5, 0],
                           name="OrangeLight")
        print(f"Created point light: {result}")

    finally:
        client.disconnect()


# ============================================================================
# Example 6: Create a Simple Scene
# ============================================================================

def example_simple_scene():
    """Create a complete simple scene."""
    print("\n" + "="*50)
    print("Example 6: Simple Scene")
    print("="*50)

    client = BlenderMCPClient()
    client.connect()

    try:
        # Create ground plane
        client.call("create_object", type="plane", scale=[10, 10, 1], name="Ground")
        client.call("set_material", object_name="Ground", material_name="GroundMat", 
                   color=[0.2, 0.3, 0.2], roughness=1.0)

        # Create a house (simple cubes)
        # Base
        client.call("create_object", type="cube", location=[0, 0, 1], 
                   scale=[3, 3, 2], name="HouseBase")
        client.call("set_material", object_name="HouseBase", material_name="WallMat",
                   color=[0.9, 0.9, 0.8])

        # Roof (scaled cube rotated)
        client.call("create_object", type="cube", location=[0, 0, 2.5],
                   scale=[3.5, 3.5, 0.2], name="Roof")
        client.call("modify_object", name="Roof", rotation=[45, 0, 0])
        client.call("set_material", object_name="Roof", material_name="RoofMat",
                   color=[0.6, 0.3, 0.2])

        # Add lighting
        client.call("create_light", type="SUN", location=[5, 5, 10], 
                   energy=1.5, name="MainSun")

        # Add camera
        client.call("create_camera", location=[8, -8, 4], 
                   rotation=[70, 0, 45], name="HouseCamera")

        print("Simple house scene created!")

        # Show final scene info
        info = client.call("get_scene_info")
        print(f"Total objects: {info['object_count']}")

    finally:
        client.disconnect()


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("Blender MCP Client Examples")
    print("="*50)
    print("Make sure Blender MCP server is running:")
    print("  blender --background --python websocket_server.py")
    print("="*50)

    # Run examples
    try:
        example_create_objects()
        example_scene_info()
        example_modify_objects()
        example_materials()
        example_lights_cameras()
        example_simple_scene()

        print("\n" + "="*50)
        print("All examples completed!")
        print("="*50)

    except ConnectionRefusedError:
        print("\nError: Could not connect to Blender MCP server.")
        print("Make sure the server is running:")
        print("  blender --background --python server/websocket_server.py")
    except Exception as e:
        print(f"\nError: {e}")
