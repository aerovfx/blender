#!/usr/bin/env python3
"""
Advanced usage examples for Blender MCP Server.

Demonstrates complex automation scenarios.
"""

import json
import websocket
import random
import math
from typing import Optional


class AdvancedBlenderClient:
    """Advanced client with helper methods."""

    def __init__(self, host="localhost", port=8765):
        self.url = f"ws://{host}:{port}"
        self.ws = None
        self._id = 0

    def connect(self):
        self.ws = websocket.create_connection(self.url, timeout=10)
        self.ws.recv()  # Welcome message
        return self

    def disconnect(self):
        if self.ws:
            self.ws.close()

    def _next_id(self):
        self._id += 1
        return self._id

    def call(self, method, **params):
        request = {
            "type": "request",
            "id": self._next_id(),
            "method": method,
            "params": params
        }
        self.ws.send(json.dumps(request))
        response = json.loads(self.ws.recv())
        if response.get("type") == "error":
            raise Exception(response.get("error"))
        return response.get("result")

    # Helper methods
    def create_grid(self, rows: int, cols: int, spacing: float, obj_type: str = "cube"):
        """Create a grid of objects."""
        objects = []
        for i in range(rows):
            for j in range(cols):
                x = (i - rows/2) * spacing
                y = (j - cols/2) * spacing
                result = self.call("create_object", 
                                 type=obj_type, 
                                 location=[x, y, 0],
                                 name=f"{obj_type}_{i}_{j}")
                objects.append(result)
        return objects

    def create_circle(self, count: int, radius: float, obj_type: str = "cube"):
        """Create objects in a circle pattern."""
        objects = []
        for i in range(count):
            angle = (i / count) * 2 * math.pi
            x = math.cos(angle) * radius
            y = math.sin(angle) * radius
            result = self.call("create_object",
                             type=obj_type,
                             location=[x, y, 0],
                             rotation=[0, 0, math.degrees(angle)],
                             name=f"{obj_type}_circle_{i}")
            objects.append(result)
        return objects

    def create_staircase(self, steps: int, rise: float, run: float, width: float):
        """Create a staircase."""
        objects = []
        for i in range(steps):
            result = self.call("create_object",
                             type="cube",
                             location=[i * run, 0, i * rise],
                             scale=[width, run, rise],
                             name=f"step_{i}")
            objects.append(result)
        return objects


# ============================================================================
# Example 1: Procedural City Generation
# ============================================================================

def example_procedural_city():
    """Generate a simple procedural city."""
    print("\n" + "="*50)
    print("Example: Procedural City")
    print("="*50)

    client = AdvancedBlenderClient()
    client.connect()

    try:
        # Create ground
        client.call("create_object", type="plane", scale=[50, 50, 1], name="Ground")
        client.call("set_material", object_name="Ground", material_name="Asphalt",
                   color=[0.2, 0.2, 0.25], roughness=0.9)

        # Create buildings in a grid
        building_count = 0
        for i in range(-4, 5):
            for j in range(-4, 5):
                # Skip some lots for streets
                if random.random() < 0.2:
                    continue

                x = i * 10
                y = j * 10

                # Random building dimensions
                width = random.uniform(3, 6)
                depth = random.uniform(3, 6)
                height = random.uniform(5, 20)

                # Create building
                name = f"Building_{building_count}"
                client.call("create_object",
                          type="cube",
                          location=[x, y, height/2],
                          scale=[width, depth, height],
                          name=name)

                # Random building color
                color = [random.uniform(0.3, 0.8) for _ in range(3)]
                client.call("set_material",
                          object_name=name,
                          material_name=f"BuildingMat_{building_count}",
                          color=color,
                          roughness=0.5)

                building_count += 1

        print(f"Created city with {building_count} buildings")

        # Add sun
        client.call("create_light", type="SUN", location=[50, 50, 100],
                   energy=2.0, name="CitySun")

        # Add camera
        client.call("create_camera", location=[60, -60, 40],
                   rotation=[60, 0, 45], name="CityCamera")

    finally:
        client.disconnect()


# ============================================================================
# Example 2: Solar System Model
# ============================================================================

def example_solar_system():
    """Create a solar system model."""
    print("\n" + "="*50)
    print("Example: Solar System")
    print("="*50)

    client = AdvancedBlenderClient()
    client.connect()

    try:
        # Sun
        client.call("create_object", type="sphere", radius=2, name="Sun")
        client.call("set_material", object_name="Sun", material_name="SunMat",
                   color=[1, 0.9, 0.5])
        client.call("create_light", type="POINT", energy=1000,
                   location=[0, 0, 0], name="SunLight")

        # Planets (simplified)
        planets = [
            {"name": "Mercury", "distance": 4, "radius": 0.2, "color": [0.7, 0.7, 0.7]},
            {"name": "Venus", "distance": 6, "radius": 0.35, "color": [0.9, 0.7, 0.5]},
            {"name": "Earth", "distance": 8, "radius": 0.4, "color": [0.2, 0.5, 0.9]},
            {"name": "Mars", "distance": 10, "radius": 0.3, "color": [0.8, 0.3, 0.2]},
            {"name": "Jupiter", "distance": 14, "radius": 1.0, "color": [0.8, 0.7, 0.5]},
            {"name": "Saturn", "distance": 18, "radius": 0.8, "color": [0.9, 0.8, 0.6]},
            {"name": "Uranus", "distance": 22, "radius": 0.6, "color": [0.6, 0.8, 0.9]},
            {"name": "Neptune", "distance": 26, "radius": 0.55, "color": [0.3, 0.4, 0.9]},
        ]

        for planet in planets:
            # Create planet
            client.call("create_object",
                      type="sphere",
                      radius=planet["radius"],
                      location=[planet["distance"], 0, 0],
                      name=planet["name"])
            client.call("set_material",
                      object_name=planet["name"],
                      material_name=f"{planet['name']}Mat",
                      color=planet["color"])

        print(f"Created solar system with {len(planets)} planets")

    finally:
        client.disconnect()


# ============================================================================
# Example 3: Animation Keyframes
# ============================================================================

def example_animation_setup():
    """Set up a simple animation scene."""
    print("\n" + "="*50)
    print("Example: Animation Setup")
    print("="*50)

    client = AdvancedBlenderClient()
    client.connect()

    try:
        import bpy
        # Note: For actual animation, you'd need direct bpy access
        # This shows the scene setup part

        # Create a bouncing ball
        client.call("create_object", type="sphere", radius=0.5, 
                   location=[0, 0, 5], name="BouncingBall")
        client.call("set_material", object_name="BouncingBall", 
                   material_name="BallMat", color=[1, 0.2, 0.2])

        # Create ground
        client.call("create_object", type="plane", scale=[10, 10, 1], 
                   name="Ground")
        client.call("set_material", object_name="Ground", 
                   material_name="GroundMat", color=[0.3, 0.3, 0.3])

        # Create cameras for different angles
        client.call("create_camera", location=[10, 10, 5], 
                   rotation=[45, 0, 45], name="Camera1")
        client.call("create_camera", location=[0, 15, 2], 
                   rotation=[80, 0, 0], name="Camera2")

        # Add lights
        client.call("create_light", type="SUN", location=[5, 5, 10],
                   energy=1.5, name="MainLight")
        client.call("create_light", type="AREA", location=[-5, -5, 5],
                   energy=50, name="FillLight")

        print("Animation scene setup complete!")
        print("Note: For keyframe animation, use direct bpy access")

    finally:
        client.disconnect()


# ============================================================================
# Example 4: Batch Export
# ============================================================================

def example_batch_export():
    """Export all objects as separate files."""
    print("\n" + "="*50)
    print("Example: Batch Export")
    print("="*50)

    client = AdvancedBlenderClient()
    client.connect()

    try:
        # First, get scene info
        info = client.call("get_scene_info")
        objects = info.get("objects", [])

        print(f"Found {len(objects)} objects in scene")

        # Export each object
        for obj in objects:
            if obj["type"] == "MESH":
                # Note: Actual batch export would need more complex logic
                # This is a simplified example
                print(f"  Would export: {obj['name']}")

        print("Batch export complete (simulation)")

    finally:
        client.disconnect()


# ============================================================================
# Example 5: Fractal Tree
# ============================================================================

def example_fractal_tree():
    """Create a fractal tree structure."""
    print("\n" + "="*50)
    print("Example: Fractal Tree")
    print("="*50)

    client = AdvancedBlenderClient()
    client.connect()

    try:
        def create_branch(start_pos, angle, length, depth, max_depth):
            if depth >= max_depth or length < 0.2:
                return

            # Calculate end position
            end_x = start_pos[0] + math.cos(angle) * length
            end_y = start_pos[1] + math.sin(angle) * length
            end_z = start_pos[2] + length * 0.5

            # Create branch
            name = f"branch_{depth}_{random.randint(0, 999)}"
            client.call("create_object",
                      type="cylinder",
                      location=[(start_pos[0] + end_x)/2, 
                               (start_pos[1] + end_y)/2, 
                               end_z],
                      radius=length * 0.1,
                      depth=length,
                      name=name)

            # Create branches
            new_length = length * 0.7
            create_branch([end_x, end_y, end_z], angle - 0.5, new_length, depth + 1, max_depth)
            create_branch([end_x, end_y, end_z], angle + 0.5, new_length, depth + 1, max_depth)

        # Start the tree
        create_branch([0, 0, 0], math.pi/2, 3, 0, 5)

        print("Fractal tree created!")

    finally:
        client.disconnect()


# ============================================================================
# Example 6: Material Library
# ============================================================================

def example_material_library():
    """Create a library of different materials."""
    print("\n" + "="*50)
    print("Example: Material Library")
    print("="*50)

    client = AdvancedBlenderClient()
    client.connect()

    try:
        materials = [
            {"name": "RedPlastic", "color": [0.8, 0.1, 0.1], "metallic": 0.0, "roughness": 0.5},
            {"name": "BlueMetal", "color": [0.1, 0.2, 0.8], "metallic": 0.9, "roughness": 0.2},
            {"name": "Gold", "color": [1.0, 0.8, 0.2], "metallic": 1.0, "roughness": 0.3},
            {"name": "Silver", "color": [0.9, 0.9, 0.9], "metallic": 1.0, "roughness": 0.4},
            {"name": "Wood", "color": [0.4, 0.3, 0.2], "metallic": 0.0, "roughness": 0.8},
            {"name": "Glass", "color": [0.9, 0.95, 1.0], "metallic": 0.0, "roughness": 0.0},
            {"name": "BlackRubber", "color": [0.05, 0.05, 0.05], "metallic": 0.0, "roughness": 0.9},
            {"name": "Copper", "color": [0.95, 0.5, 0.3], "metallic": 1.0, "roughness": 0.4},
        ]

        # Create spheres with different materials
        for i, mat in enumerate(materials):
            x = (i % 4) * 3
            y = (i // 4) * 3
            name = f"Sphere_{mat['name']}"
            
            client.call("create_object",
                      type="sphere",
                      radius=0.8,
                      location=[x, y, 1],
                      name=name)
            client.call("set_material",
                      object_name=name,
                      material_name=mat["name"],
                      color=mat["color"],
                      metallic=mat["metallic"],
                      roughness=mat["roughness"])

        print(f"Created {len(materials)} material samples")

    finally:
        client.disconnect()


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("Blender MCP Advanced Examples")
    print("="*50)

    examples = {
        "1": ("Procedural City", example_procedural_city),
        "2": ("Solar System", example_solar_system),
        "3": ("Animation Setup", example_animation_setup),
        "4": ("Fractal Tree", example_fractal_tree),
        "5": ("Material Library", example_material_library),
    }

    print("\nAvailable examples:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    print("  a. Run all examples")
    print("="*50)

    choice = input("Select example (or 'a' for all): ").strip().lower()

    try:
        if choice == "a":
            for _, (_, func) in examples.items():
                try:
                    func()
                except ConnectionRefusedError:
                    print("Connection failed. Make sure server is running.")
                    break
        elif choice in examples:
            examples[choice][1]()
        else:
            print("Invalid choice")

    except ConnectionRefusedError:
        print("\nError: Could not connect to Blender MCP server.")
        print("Start with: blender --background --python server/websocket_server.py")
    except Exception as e:
        print(f"\nError: {e}")
