# Blender Embedded Engine - Next Steps Guide

Hướng dẫn chi tiết các bước tiếp theo sau khi đã chạy thành công Blender Embedded Engine.

---

## 📋 Table of Contents

1. [Test Engine & Verify](#1-test-engine--verify)
2. [Customize Objects & Materials](#2-customize-objects--materials)
3. [Integrate vào Pipeline](#3-integrate-vào-pipeline)
4. [Extend với Animation & Batch Render](#4-extend-với-animation--batch-render)

---

## 1. Test Engine & Verify

### 1.1 Chạy Engine lần đầu

```bash
cd /Users/pixibox/blender/blender-mcp

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy engine
blender --background --python server/embedded_engine.py -- --port 8765
```

### 1.2 Verify Web Interface

Mở trình duyệt: `http://localhost:8765`

**Checklist:**
- [ ] Web interface load thành công
- [ ] Status dot màu xanh (connected)
- [ ] Viewport hiển thị (gradient background)
- [ ] Activity log hiển thị message
- [ ] Statistics panel hiển thị uptime

### 1.3 Test Create Objects

Click các buttons trong toolbar:

```
📦 Cube → Check log: "Creating cube"
🔮 Sphere → Check log: "Creating sphere"
🛢️ Cylinder → Check log: "Creating cylinder"
```

**Verify:**
- [ ] Object được tạo trong viewport
- [ ] Object list cập nhật
- [ ] Statistics "Objects" tăng lên

### 1.4 Test API với curl

```bash
# Test 1: Get stats
curl http://localhost:8765/api/stats | python -m json.tool

# Test 2: Get scene info
curl -X POST http://localhost:8765/api/command \
  -H "Content-Type: application/json" \
  -d '{"method": "get_scene_info"}' | python -m json.tool

# Test 3: Create cube
curl -X POST http://localhost:8765/api/command \
  -H "Content-Type: application/json" \
  -d '{
    "method": "create_object",
    "params": {
      "type": "cube",
      "location": [0, 0, 0],
      "name": "TestCube"
    }
  }' | python -m json.tool

# Test 4: Render viewport
curl -X POST http://localhost:8765/api/command \
  -H "Content-Type: application/json" \
  -d '{"method": "render_viewport", "params": {"format": "PNG"}}' \
  -o response.json

# Extract and view image
python -c "
import json, base64
with open('response.json') as f:
    data = json.load(f)
    img = data['image'].split(',')[1]
    with open('viewport.png', 'wb') as imgf:
        imgf.write(base64.b64decode(img))
print('Saved viewport.png')
"
```

### 1.5 Test với Python Script

```bash
# Run automated test
python examples/test_embedded_engine.py
```

**Expected Output:**
```
============================================================
🧪 Blender Embedded Engine Test
============================================================

[1/6] Checking server status...
✓ Server running
  Uptime: 45.2s
  Renders: 12

[2/6] Getting scene info...
✓ Scene: Scene
  Objects: 3
  Frame: 1

[3/6] Creating test objects...
✓ Created cube: TestCube
✓ Created sphere: TestSphere
✓ Created cylinder: TestCylinder

[4/6] Rendering viewport...
✓ Viewport rendered
  Resolution: 1280x720
  Image size: 45678 bytes
  Saved to: test_viewport.png

[5/6] Modifying object...
✓ Object modified
  New location: [5.0, 0.0, 0.0]
  New scale: [2.0, 2.0, 2.0]

[6/6] Getting updated scene info...
✓ Updated scene
  Total objects: 6

============================================================
✅ Test Complete!
============================================================
```

### 1.6 Troubleshooting

**Lỗi: Cannot connect to server**
```bash
# Check if server is running
curl http://localhost:8765/api/stats

# Check port
lsof -i :8765

# Restart server
pkill -f embedded_engine
blender --background --python server/embedded_engine.py -- --port 8765
```

**Lỗi: Module not found**
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

---

## 2. Customize Objects & Materials

### 2.1 Tạo Custom Objects Script

**File: `custom_objects.py`**

```python
#!/usr/bin/env python3
"""
Custom object creation examples for Blender Embedded Engine
"""

import requests
import json

BASE_URL = "http://localhost:8765"

def create_scene():
    """Create a custom scene with various objects"""
    
    # Clear existing objects
    requests.post(f"{BASE_URL}/api/command", json={
        "method": "clear_scene",
        "params": {"confirm": True}
    })
    
    # Create ground plane
    requests.post(f"{BASE_URL}/api/command", json={
        "method": "create_object",
        "params": {
            "type": "plane",
            "scale": [10, 10, 1],
            "name": "Ground"
        }
    })
    
    # Create buildings (cubes)
    buildings = [
        {"location": [-5, -5, 2.5], "scale": [3, 3, 5], "name": "Building_1"},
        {"location": [0, -5, 4], "scale": [4, 4, 8], "name": "Building_2"},
        {"location": [5, -5, 3], "scale": [3, 3, 6], "name": "Building_3"},
    ]
    
    for b in buildings:
        requests.post(f"{BASE_URL}/api/command", json={
            "method": "create_object",
            "params": {
                "type": "cube",
                **b
            }
        })
    
    # Create trees (cylinder + sphere)
    for i, pos in enumerate([[-8, 8, 0], [0, 8, 0], [8, 8, 0]]):
        # Trunk
        requests.post(f"{BASE_URL}/api/command", json={
            "method": "create_object",
            "params": {
                "type": "cylinder",
                "location": pos,
                "radius": 0.3,
                "depth": 2,
                "name": f"Tree_{i}_trunk"
            }
        })
        # Crown
        requests.post(f"{BASE_URL}/api/command", json={
            "method": "create_object",
            "params": {
                "type": "sphere",
                "location": [pos[0], pos[1], pos[2] + 3],
                "radius": 1.5,
                "name": f"Tree_{i}_crown"
            }
        })
    
    # Create sun light
    requests.post(f"{BASE_URL}/api/command", json={
        "method": "create_object",
        "params": {
            "type": "light",
            "light_type": "SUN",
            "location": [10, 10, 20],
            "name": "Sun"
        }
    })
    
    # Create camera
    requests.post(f"{BASE_URL}/api/command", json={
        "method": "create_object",
        "params": {
            "type": "camera",
            "location": [0, -15, 8],
            "rotation": [1.3, 0, 0],
            "name": "MainCamera"
        }
    })
    
    print("✓ Custom scene created!")
    print("  - Ground plane")
    print("  - 3 buildings")
    print("  - 3 trees")
    print("  - Sun light")
    print("  - Camera")

def apply_materials():
    """Apply custom materials to objects"""
    
    materials = [
        {
            "object": "Ground",
            "material": "Grass",
            "color": [0.2, 0.6, 0.2],
            "roughness": 0.9
        },
        {
            "object": "Building_1",
            "material": "Glass",
            "color": [0.7, 0.8, 0.9],
            "metallic": 0.8,
            "roughness": 0.1
        },
        {
            "object": "Building_2",
            "material": "Concrete",
            "color": [0.5, 0.5, 0.5],
            "roughness": 0.8
        },
        {
            "object": "Tree_0_crown",
            "material": "Leaves",
            "color": [0.1, 0.4, 0.1],
            "roughness": 0.9
        },
    ]
    
    for mat in materials:
        params = {
            "object_name": mat["object"],
            "material_name": mat["material"],
            "color": mat["color"],
            "roughness": mat["roughness"]
        }
        if "metallic" in mat:
            params["metallic"] = mat["metallic"]
        
        requests.post(f"{BASE_URL}/api/command", json={
            "method": "set_material",
            "params": params
        })
    
    print("✓ Materials applied!")

if __name__ == "__main__":
    print("Creating custom scene...")
    create_scene()
    
    print("\nApplying materials...")
    apply_materials()
    
    print("\nRendering viewport...")
    response = requests.post(f"{BASE_URL}/api/command", json={
        "method": "render_viewport"
    })
    
    if response.json().get("success"):
        print("✓ Viewport rendered successfully!")
        print(f"  Resolution: {response.json()['width']}x{response.json()['height']}")
```

**Run:**
```bash
python custom_objects.py
```

### 2.2 Material Library

**File: `material_library.py`**

```python
#!/usr/bin/env python3
"""
Material library for Blender Embedded Engine
"""

import requests

BASE_URL = "http://localhost:8765"

# Pre-defined materials
MATERIALS = {
    # Metals
    "gold": {
        "color": [1.0, 0.8, 0.2],
        "metallic": 1.0,
        "roughness": 0.3
    },
    "silver": {
        "color": [0.9, 0.9, 0.9],
        "metallic": 1.0,
        "roughness": 0.4
    },
    "copper": {
        "color": [0.95, 0.5, 0.3],
        "metallic": 1.0,
        "roughness": 0.4
    },
    "steel": {
        "color": [0.7, 0.7, 0.7],
        "metallic": 0.9,
        "roughness": 0.5
    },
    
    # Non-metals
    "plastic_red": {
        "color": [0.8, 0.1, 0.1],
        "metallic": 0.0,
        "roughness": 0.5
    },
    "plastic_blue": {
        "color": [0.1, 0.2, 0.8],
        "metallic": 0.0,
        "roughness": 0.5
    },
    "plastic_black": {
        "color": [0.05, 0.05, 0.05],
        "metallic": 0.0,
        "roughness": 0.6
    },
    
    # Natural
    "wood": {
        "color": [0.4, 0.3, 0.2],
        "metallic": 0.0,
        "roughness": 0.8
    },
    "stone": {
        "color": [0.5, 0.5, 0.5],
        "metallic": 0.0,
        "roughness": 0.9
    },
    "grass": {
        "color": [0.2, 0.6, 0.2],
        "metallic": 0.0,
        "roughness": 1.0
    },
    
    # Special
    "glass": {
        "color": [0.9, 0.95, 1.0],
        "metallic": 0.0,
        "roughness": 0.0
    },
    "diamond": {
        "color": [1.0, 1.0, 1.0],
        "metallic": 0.0,
        "roughness": 0.0
    },
    "emissive_blue": {
        "color": [0.2, 0.5, 1.0],
        "metallic": 0.0,
        "roughness": 0.5
    }
}

def apply_material(object_name: str, material_name: str):
    """Apply a pre-defined material to an object"""
    
    if material_name not in MATERIALS:
        print(f"Material '{material_name}' not found")
        return False
    
    mat = MATERIALS[material_name]
    
    response = requests.post(f"{BASE_URL}/api/command", json={
        "method": "set_material",
        "params": {
            "object_name": object_name,
            "material_name": material_name,
            "color": mat["color"],
            "metallic": mat["metallic"],
            "roughness": mat["roughness"]
        }
    })
    
    result = response.json()
    if result.get("success"):
        print(f"✓ Applied {material_name} to {object_name}")
        return True
    else:
        print(f"✗ Failed: {result.get('error')}")
        return False

def list_materials():
    """List all available materials"""
    print("\nAvailable Materials:")
    print("=" * 40)
    
    categories = {
        "Metals": ["gold", "silver", "copper", "steel"],
        "Plastics": ["plastic_red", "plastic_blue", "plastic_black"],
        "Natural": ["wood", "stone", "grass"],
        "Special": ["glass", "diamond", "emissive_blue"]
    }
    
    for category, mats in categories.items():
        print(f"\n{category}:")
        for mat in mats:
            print(f"  - {mat}")

def create_material_showcase():
    """Create a showcase of all materials"""
    
    # Clear scene
    requests.post(f"{BASE_URL}/api/command", json={
        "method": "clear_scene",
        "params": {"confirm": True}
    })
    
    # Create spheres for each material
    row = 0
    col = 0
    spacing = 3
    
    for mat_name in MATERIALS.keys():
        x = col * spacing
        y = row * spacing
        
        # Create sphere
        requests.post(f"{BASE_URL}/api/command", json={
            "method": "create_object",
            "params": {
                "type": "sphere",
                "location": [x, y, 1],
                "radius": 0.8,
                "name": f"Sphere_{mat_name}"
            }
        })
        
        # Apply material
        apply_material(f"Sphere_{mat_name}", mat_name)
        
        # Move to next column
        col += 1
        if col >= 5:
            col = 0
            row += 1
    
    print(f"\n✓ Created material showcase with {len(MATERIALS)} materials")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 2:
        # Apply material to object
        obj_name = sys.argv[1]
        mat_name = sys.argv[2]
        apply_material(obj_name, mat_name)
    
    elif len(sys.argv) == 1:
        # Show materials
        list_materials()
        
        print("\nUsage:")
        print("  python material_library.py                    # List materials")
        print("  python material_library.py Cube gold          # Apply gold to Cube")
        print("  python material_library.py --showcase         # Create showcase")
    
    elif len(sys.argv) > 1 and sys.argv[1] == "--showcase":
        create_material_showcase()
```

**Run:**
```bash
# List materials
python material_library.py

# Apply material
python material_library.py Cube gold

# Create showcase
python material_library.py --showcase
```

---

## 3. Integrate vào Pipeline

### 3.1 Python Client Library

**File: `blender_client.py`**

```python
#!/usr/bin/env python3
"""
Blender Embedded Engine Client Library
"""

import requests
import time
from typing import List, Dict, Optional


class BlenderClient:
    """Client for Blender Embedded Engine"""
    
    def __init__(self, base_url: str = "http://localhost:8765"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def _command(self, method: str, **params) -> Dict:
        """Execute command and return result"""
        response = self.session.post(
            f"{self.base_url}/api/command",
            json={"method": method, "params": params},
            timeout=30
        )
        return response.json()
    
    def is_running(self) -> bool:
        """Check if engine is running"""
        try:
            response = self.session.get(f"{self.base_url}/api/stats", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    # Object Operations
    def create_cube(self, location=None, scale=None, name=None):
        return self._command("create_object", type="cube", 
                           location=location, scale=scale, name=name)
    
    def create_sphere(self, location=None, radius=None, name=None):
        return self._command("create_object", type="sphere",
                           location=location, radius=radius, name=name)
    
    def create_cylinder(self, location=None, radius=None, depth=None, name=None):
        return self._command("create_object", type="cylinder",
                           location=location, radius=radius, depth=depth, name=name)
    
    def delete_object(self, name: str):
        return self._command("delete_object", name=name)
    
    def modify_object(self, name: str, location=None, rotation=None, scale=None):
        return self._command("modify_object", name=name,
                           location=location, rotation=rotation, scale=scale)
    
    # Material Operations
    def set_material(self, object_name: str, material_name: str,
                    color=None, metallic=None, roughness=None):
        return self._command("set_material",
                           object_name=object_name,
                           material_name=material_name,
                           color=color,
                           metallic=metallic,
                           roughness=roughness)
    
    # Scene Operations
    def get_scene_info(self):
        return self._command("get_scene_info")
    
    def clear_scene(self):
        return self._command("clear_scene", confirm=True)
    
    def get_object_count(self) -> int:
        """Get number of objects in scene"""
        info = self.get_scene_info()
        return info.get("object_count", 0) if info.get("success") else 0
    
    # Rendering
    def render_viewport(self, format: str = "PNG") -> Dict:
        return self._command("render_viewport", format=format)
    
    def save_viewport(self, filepath: str, format: str = "PNG"):
        """Render viewport and save to file"""
        import base64
        
        result = self.render_viewport(format)
        if result.get("success"):
            img_data = result["image"].split(",")[1]
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(img_data))
            return True
        return False
    
    def render_final(self, filepath: str, resolution=None, samples=None):
        """Final render with Cycles"""
        params = {"filepath": filepath}
        if resolution:
            params["resolution_x"] = resolution[0]
            params["resolution_y"] = resolution[1]
        if samples:
            params["samples"] = samples
        return self._command("render_final", **params)
    
    # Batch Operations
    def batch_create(self, objects: List[Dict]):
        """Create multiple objects"""
        results = []
        for obj in objects:
            result = self.create_cube(**obj) if obj.get("type") == "cube" else \
                    self.create_sphere(**obj) if obj.get("type") == "sphere" else \
                    self.create_cylinder(**obj)
            results.append(result)
        return results
    
    def batch_export(self, directory: str, format: str = "FBX"):
        """Export all objects"""
        return self._command("batch_export", directory=directory, format=format)


# Example Usage
if __name__ == "__main__":
    client = BlenderClient()
    
    # Check connection
    if not client.is_running():
        print("❌ Blender Engine not running!")
        print("Start with: blender --background --python server/embedded_engine.py")
        exit(1)
    
    print("✓ Connected to Blender Engine")
    
    # Clear scene
    client.clear_scene()
    
    # Create objects
    client.create_cube(location=[0, 0, 0], name="Cube")
    client.create_sphere(location=[3, 0, 0], name="Sphere")
    client.create_cylinder(location=[-3, 0, 0], name="Cylinder")
    
    # Apply materials
    client.set_material("Cube", "Gold", color=[1, 0.8, 0.2], metallic=1.0)
    client.set_material("Sphere", "Plastic", color=[1, 0, 0], roughness=0.5)
    
    # Get scene info
    info = client.get_scene_info()
    print(f"\nScene: {info.get('scene_name')}")
    print(f"Objects: {info.get('object_count')}")
    
    # Save viewport
    client.save_viewport("output.png")
    print("\n✓ Saved viewport to output.png")
```

### 3.2 Production Pipeline Example

**File: `production_pipeline.py`**

```python
#!/usr/bin/env python3
"""
Production Pipeline Example
Automated product visualization workflow
"""

from blender_client import BlenderClient
import os
from datetime import datetime


class ProductVisualizationPipeline:
    """Automated product visualization pipeline"""
    
    def __init__(self, output_dir: str = "./renders"):
        self.client = BlenderClient()
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def setup_studio(self):
        """Setup studio environment"""
        print("🎬 Setting up studio...")
        
        # Clear scene
        self.client.clear_scene()
        
        # Create cyclorama (curved backdrop)
        self.client.create_cube(
            location=[0, 0, -5],
            scale=[20, 20, 10],
            name="Backdrop"
        )
        self.client.set_material("Backdrop", "White", 
                               color=[0.95, 0.95, 0.95], roughness=0.9)
        
        # Create floor
        self.client.create_plane(
            location=[0, 0, -10],
            scale=[20, 20, 1],
            name="Floor"
        )
        self.client.set_material("Floor", "Marble",
                               color=[0.9, 0.9, 0.9], metallic=0.1, roughness=0.2)
        
        # Add three-point lighting
        self.client.create_light(location=[10, 10, 10], name="KeyLight")
        self.client.create_light(location=[-10, 5, 5], name="FillLight")
        self.client.create_light(location=[0, -15, 15], name="RimLight")
        
        # Setup camera
        self.client.create_camera(
            location=[0, -15, 5],
            rotation=[1.4, 0, 0],
            focal_length=85,
            name="MainCamera"
        )
        
        print("✓ Studio setup complete")
    
    def add_product(self, product_file: str = None):
        """Add product to scene"""
        print("📦 Adding product...")
        
        if product_file:
            # Import product file (FBX, OBJ, etc.)
            # This would need additional implementation
            print(f"  Importing: {product_file}")
        else:
            # Use placeholder (product box)
            self.client.create_cube(
                location=[0, 0, 0],
                scale=[2, 2, 3],
                name="Product"
            )
            self.client.set_material("Product", "ProductMat",
                                   color=[0.2, 0.3, 0.8], roughness=0.5)
        
        print("✓ Product added")
    
    def render_turntable(self, frames: int = 36, output_name: str = "turntable"):
        """Render turntable animation"""
        print(f"🎥 Rendering turntable ({frames} frames)...")
        
        for i in range(frames):
            angle = (i / frames) * 360
            
            # Rotate product
            # (Would need rotation API implementation)
            
            # Render frame
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"{self.output_dir}/{output_name}_{i:03d}_{timestamp}.png"
            
            self.client.render_final(
                filepath=filepath,
                resolution=(1920, 1080),
                samples=128
            )
            
            print(f"  Frame {i+1}/{frames}: {filepath}")
        
        print("✓ Turntable complete")
    
    def render_beauty_shot(self, output_name: str = "beauty"):
        """Render final beauty shot"""
        print("📸 Rendering beauty shot...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"{self.output_dir}/{output_name}_{timestamp}.png"
        
        self.client.render_final(
            filepath=filepath,
            resolution=(1920, 1080),
            samples=256
        )
        
        print(f"✓ Beauty shot: {filepath}")
        return filepath
    
    def run(self, product_file: str = None):
        """Run complete pipeline"""
        print("=" * 60)
        print("🎬 Product Visualization Pipeline")
        print("=" * 60)
        
        # Check connection
        if not self.client.is_running():
            print("❌ Blender Engine not running!")
            return
        
        # Run pipeline
        self.setup_studio()
        self.add_product(product_file)
        self.render_beauty_shot()
        # self.render_turntable(frames=36)
        
        print("\n" + "=" * 60)
        print("✅ Pipeline Complete!")
        print("=" * 60)
        print(f"Output directory: {self.output_dir}")


if __name__ == "__main__":
    pipeline = ProductVisualizationPipeline()
    pipeline.run()
```

**Run:**
```bash
python production_pipeline.py
```

---

## 4. Extend với Animation & Batch Render

### 4.1 Animation System

**File: `animation_system.py`**

```python
#!/usr/bin/env python3
"""
Animation System for Blender Embedded Engine
"""

import requests
import time
from typing import List, Dict


class AnimationSystem:
    """Keyframe animation system"""
    
    def __init__(self, base_url: str = "http://localhost:8765"):
        self.base_url = base_url
        self.keyframes = []
    
    def _command(self, method: str, **params):
        """Execute command"""
        response = requests.post(
            f"{self.base_url}/api/command",
            json={"method": method, "params": params}
        )
        return response.json()
    
    def add_keyframe(self, object_name: str, frame: int,
                    location=None, rotation=None, scale=None):
        """Add keyframe for object"""
        self.keyframes.append({
            "object": object_name,
            "frame": frame,
            "location": location,
            "rotation": rotation,
            "scale": scale
        })
    
    def animate_bouncing_ball(self, object_name: str, 
                             start_frame: int = 1,
                             end_frame: int = 60,
                             bounces: int = 3,
                             height: float = 5.0):
        """Create bouncing ball animation"""
        print(f"🎬 Creating bouncing ball animation...")
        
        frame_range = end_frame - start_frame
        bounce_interval = frame_range / bounces
        
        for bounce in range(bounces + 1):
            # Ground contact
            contact_frame = int(start_frame + bounce * bounce_interval)
            self.add_keyframe(object_name, contact_frame, location=[0, 0, 0])
            
            # Peak (if not last bounce)
            if bounce < bounces:
                peak_frame = int(contact_frame + bounce_interval / 2)
                peak_height = height * (0.7 ** bounce)
                self.add_keyframe(object_name, peak_frame, 
                                location=[0, 0, peak_height])
        
        # Execute keyframes
        self._execute_keyframes()
        print(f"✓ Created {len(self.keyframes)} keyframes")
    
    def animate_orbit(self, object_name: str, center=None,
                     radius: float = 10, frames: int = 90):
        """Create orbit animation"""
        import math
        
        print(f"🎬 Creating orbit animation...")
        
        if center is None:
            center = [0, 0, 0]
        
        for frame in range(frames):
            angle = (frame / frames) * 2 * math.pi
            x = center[0] + math.cos(angle) * radius
            y = center[1] + math.sin(angle) * radius
            z = center[2]
            
            self.add_keyframe(object_name, frame, location=[x, y, z])
        
        self._execute_keyframes()
        print(f"✓ Created orbit animation ({frames} frames)")
    
    def _execute_keyframes(self):
        """Execute all keyframes"""
        # Sort by frame
        self.keyframes.sort(key=lambda k: k["frame"])
        
        # Apply each keyframe
        for kf in self.keyframes:
            params = {
                "name": kf["object"],
                "frame": kf["frame"]
            }
            if kf.get("location"):
                params["location"] = kf["location"]
            if kf.get("rotation"):
                params["rotation"] = kf["rotation"]
            if kf.get("scale"):
                params["scale"] = kf["scale"]
            
            # Note: This requires keyframe API implementation in engine
            # For now, just modify object
            if "location" in params:
                self._command("modify_object", 
                            name=kf["object"], 
                            location=params["location"])
    
    def render_animation(self, output_dir: str, 
                        start_frame: int, end_frame: int,
                        resolution=(1920, 1080)):
        """Render animation sequence"""
        print(f"🎥 Rendering animation ({start_frame}-{end_frame})...")
        
        from blender_client import BlenderClient
        client = BlenderClient(self.base_url)
        
        for frame in range(start_frame, end_frame + 1):
            # Set frame
            self._command("set_frame", frame=frame)
            
            # Render
            filepath = f"{output_dir}/frame_{frame:04d}.png"
            client.render_final(filepath, resolution=resolution)
            
            print(f"  Frame {frame}: {filepath}")
        
        print(f"✓ Rendered {end_frame - start_frame + 1} frames")


if __name__ == "__main__":
    anim = AnimationSystem()
    
    # Create bouncing ball
    anim.animate_bouncing_ball("Sphere", start_frame=1, end_frame=60, bounces=3)
    
    # Render animation
    anim.render_animation("./animation", 1, 60)
```

### 4.2 Batch Render System

**File: `batch_render.py`**

```python
#!/usr/bin/env python3
"""
Batch Render System
"""

import requests
import json
import os
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict


class BatchRenderer:
    """Batch render multiple scenes/frames"""
    
    def __init__(self, base_url: str = "http://localhost:8765",
                 workers: int = 1):
        self.base_url = base_url
        self.workers = workers
        self.queue = []
    
    def _command(self, method: str, **params):
        """Execute command"""
        response = requests.post(
            f"{self.base_url}/api/command",
            json={"method": method, "params": params}
        )
        return response.json()
    
    def add_job(self, scene: str, frame_range: tuple, 
                output_dir: str, resolution=(1920, 1080)):
        """Add render job to queue"""
        self.queue.append({
            "scene": scene,
            "frames": range(frame_range[0], frame_range[1] + 1),
            "output_dir": output_dir,
            "resolution": resolution
        })
    
    def render_frame(self, scene: str, frame: int, 
                    output_dir: str, resolution) -> Dict:
        """Render single frame"""
        import time
        
        # Set scene
        # Set frame
        self._command("set_frame", frame=frame)
        
        # Render
        filepath = f"{output_dir}/{scene}_{frame:04d}.png"
        result = self._command("render_final", 
                              filepath=filepath,
                              resolution_x=resolution[0],
                              resolution_y=resolution[1])
        
        return {
            "scene": scene,
            "frame": frame,
            "filepath": filepath,
            "success": result.get("success", False)
        }
    
    def render_job(self, job: Dict) -> List[Dict]:
        """Render all frames in a job"""
        results = []
        
        # Create output directory
        os.makedirs(job["output_dir"], exist_ok=True)
        
        # Render each frame
        for frame in job["frames"]:
            result = self.render_frame(
                job["scene"],
                frame,
                job["output_dir"],
                job["resolution"]
            )
            results.append(result)
            print(f"  Rendered {job['scene']} frame {frame}")
        
        return results
    
    def render_all(self) -> Dict:
        """Render all jobs in queue"""
        print(f"🎬 Starting batch render ({len(self.queue)} jobs)...")
        
        all_results = []
        
        # Sequential rendering (single Blender instance)
        for job in self.queue:
            print(f"\nJob: {job['scene']}")
            results = self.render_job(job)
            all_results.extend(results)
        
        # Summary
        successful = sum(1 for r in all_results if r["success"])
        failed = len(all_results) - successful
        
        print("\n" + "=" * 60)
        print("Batch Render Complete")
        print(f"  Total frames: {len(all_results)}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print("=" * 60)
        
        return {
            "total": len(all_results),
            "successful": successful,
            "failed": failed,
            "results": all_results
        }


if __name__ == "__main__":
    renderer = BatchRenderer()
    
    # Add jobs
    renderer.add_job("Scene_1", (1, 100), "./renders/scene1")
    renderer.add_job("Scene_2", (1, 50), "./renders/scene2")
    
    # Render all
    results = renderer.render_all()
```

---

## 📊 Summary

### Checklist hoàn thành:

```
Phase 1 - Test Engine:
✓ Chạy embedded_engine.py
✓ Verify web interface
✓ Test create objects
✓ Test API với curl
✓ Test với Python script

Phase 2 - Customize:
✓ Custom objects script
✓ Material library
✓ Apply materials

Phase 3 - Integrate:
✓ Python client library
✓ Production pipeline example

Phase 4 - Extend:
✓ Animation system
✓ Batch render system
```

### Next Actions:

1. **Run tests** - Execute tất cả scripts
2. **Customize** - Tạo scene riêng của bạn
3. **Integrate** - Kết nối vào workflow hiện có
4. **Extend** - Thêm features mới

---

**🎉 Bạn đã hoàn thành các bước tiếp theo của Blender Embedded Engine!**
