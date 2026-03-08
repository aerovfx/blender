#!/usr/bin/env python3
"""
Quick test script for Blender Embedded Engine.

Run this after starting the engine to verify it works.
"""

import requests
import json
import time


def test_engine(base_url="http://localhost:8765"):
    """Test the embedded engine"""
    
    print("=" * 60)
    print("🧪 Blender Embedded Engine Test")
    print("=" * 60)
    
    # Test 1: Check server is running
    print("\n[1/6] Checking server status...")
    try:
        response = requests.get(f"{base_url}/api/stats", timeout=5)
        stats = response.json()
        print(f"✓ Server running")
        print(f"  Uptime: {stats.get('uptime_seconds', 0):.1f}s")
        print(f"  Renders: {stats.get('render_count', 0)}")
    except Exception as e:
        print(f"✗ Server not responding: {e}")
        return False
    
    # Test 2: Get scene info
    print("\n[2/6] Getting scene info...")
    response = requests.post(f"{base_url}/api/command", json={
        "method": "get_scene_info"
    })
    result = response.json()
    if result.get("success"):
        print(f"✓ Scene: {result.get('scene_name')}")
        print(f"  Objects: {result.get('object_count')}")
        print(f"  Frame: {result.get('frame_current')}")
    else:
        print(f"✗ Failed: {result.get('error')}")
    
    # Test 3: Create objects
    print("\n[3/6] Creating test objects...")
    objects = [
        {"type": "cube", "location": [0, 0, 0], "name": "TestCube"},
        {"type": "sphere", "location": [2, 0, 0], "name": "TestSphere"},
        {"type": "cylinder", "location": [-2, 0, 0], "name": "TestCylinder"},
    ]
    
    for obj in objects:
        response = requests.post(f"{base_url}/api/command", json={
            "method": "create_object",
            "params": obj
        })
        result = response.json()
        if result.get("success"):
            print(f"✓ Created {obj['type']}: {result.get('object_name')}")
        else:
            print(f"✗ Failed to create {obj['type']}: {result.get('error')}")
    
    # Test 4: Render viewport
    print("\n[4/6] Rendering viewport...")
    response = requests.post(f"{base_url}/api/command", json={
        "method": "render_viewport"
    })
    result = response.json()
    if result.get("success"):
        print(f"✓ Viewport rendered")
        print(f"  Resolution: {result.get('width')}x{result.get('height')}")
        print(f"  Image size: {len(result.get('image', ''))} bytes")
        
        # Save image
        if result.get("image"):
            import base64
            img_data = result["image"].split(",")[1]
            with open("test_viewport.png", "wb") as f:
                f.write(base64.b64decode(img_data))
            print(f"  Saved to: test_viewport.png")
    else:
        print(f"✗ Render failed: {result.get('error')}")
    
    # Test 5: Modify object
    print("\n[5/6] Modifying object...")
    response = requests.post(f"{base_url}/api/command", json={
        "method": "modify_object",
        "params": {
            "name": "TestCube",
            "location": [5, 0, 0],
            "scale": [2, 2, 2]
        }
    })
    result = response.json()
    if result.get("success"):
        print(f"✓ Object modified")
        print(f"  New location: {result.get('location')}")
        print(f"  New scale: {result.get('scale')}")
    else:
        print(f"✗ Modify failed: {result.get('error')}")
    
    # Test 6: Get updated scene info
    print("\n[6/6] Getting updated scene info...")
    response = requests.post(f"{base_url}/api/command", json={
        "method": "get_scene_info"
    })
    result = response.json()
    if result.get("success"):
        print(f"✓ Updated scene")
        print(f"  Total objects: {result.get('object_count')}")
        for obj in result.get("objects", [])[:5]:
            print(f"    - {obj['name']} ({obj['type']})")
    else:
        print(f"✗ Failed: {result.get('error')}")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ Test Complete!")
    print("=" * 60)
    print(f"\nWeb Interface: {base_url}")
    print(f"Viewport Stream: {base_url}/ws")
    print(f"API Endpoint: {base_url}/api/command")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Blender Embedded Engine")
    parser.add_argument("--url", default="http://localhost:8765", 
                       help="Engine base URL")
    args = parser.parse_args()
    
    try:
        test_engine(args.url)
    except requests.exceptions.ConnectionError:
        print("\n✗ Cannot connect to engine")
        print("\nStart the engine first:")
        print("  blender --background --python embedded_engine.py")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
