#!/usr/bin/env python3
"""
Quick test script for Blender MCP Server.

Run this after starting the WebSocket server to verify everything works.
"""

import json
import sys

try:
    import websocket
except ImportError:
    print("Error: websocket-client package not installed")
    print("Install with: pip install websocket-client")
    sys.exit(1)


def test_connection(host="localhost", port=8765):
    """Test basic connection."""
    print(f"Connecting to ws://{host}:{port}...")
    
    ws = websocket.create_connection(f"ws://{host}:{port}", timeout=5)
    
    # Get welcome message
    welcome = json.loads(ws.recv())
    print(f"✓ Connected: {welcome.get('message', 'Unknown')}")
    ws.close()
    return True


def test_ping(host="localhost", port=8765):
    """Test ping/pong."""
    print("Testing ping...")
    
    ws = websocket.create_connection(f"ws://{host}:{port}", timeout=5)
    ws.recv()  # Welcome
    
    ws.send(json.dumps({"type": "ping", "id": 1}))
    response = json.loads(ws.recv())
    
    if response.get("type") == "pong":
        print("✓ Ping successful")
        ws.close()
        return True
    else:
        print(f"✗ Unexpected response: {response}")
        ws.close()
        return False


def test_create_object(host="localhost", port=8765):
    """Test object creation."""
    print("Testing object creation...")
    
    ws = websocket.create_connection(f"ws://{host}:{port}", timeout=5)
    ws.recv()  # Welcome
    
    request = {
        "type": "request",
        "id": 1,
        "method": "create_object",
        "params": {
            "type": "cube",
            "location": [0, 0, 0],
            "name": "TestCube"
        }
    }
    
    ws.send(json.dumps(request))
    response = json.loads(ws.recv())
    
    if response.get("type") == "response" and response.get("result", {}).get("success"):
        print("✓ Object creation successful")
        ws.close()
        return True
    else:
        print(f"✗ Object creation failed: {response}")
        ws.close()
        return False


def test_get_scene_info(host="localhost", port=8765):
    """Test getting scene info."""
    print("Testing scene info...")
    
    ws = websocket.create_connection(f"ws://{host}:{port}", timeout=5)
    ws.recv()  # Welcome
    
    request = {
        "type": "request",
        "id": 1,
        "method": "get_scene_info"
    }
    
    ws.send(json.dumps(request))
    response = json.loads(ws.recv())
    
    if response.get("type") == "response":
        result = response.get("result", {})
        print(f"✓ Scene info retrieved: {result.get('object_count', 0)} objects")
        ws.close()
        return True
    else:
        print(f"✗ Scene info failed: {response}")
        ws.close()
        return False


def test_modify_object(host="localhost", port=8765):
    """Test object modification."""
    print("Testing object modification...")
    
    ws = websocket.create_connection(f"ws://{host}:{port}", timeout=5)
    ws.recv()  # Welcome
    
    # First create an object to modify
    ws.send(json.dumps({
        "type": "request",
        "id": 1,
        "method": "create_object",
        "params": {"type": "sphere", "name": "TestSphere"}
    }))
    ws.recv()
    
    # Now modify it
    ws.send(json.dumps({
        "type": "request",
        "id": 2,
        "method": "modify_object",
        "params": {
            "name": "TestSphere",
            "location": [5, 5, 5]
        }
    }))
    response = json.loads(ws.recv())
    
    if response.get("type") == "response" and response.get("result", {}).get("success"):
        print("✓ Object modification successful")
        ws.close()
        return True
    else:
        print(f"✗ Object modification failed: {response}")
        ws.close()
        return False


def test_materials(host="localhost", port=8765):
    """Test material creation."""
    print("Testing materials...")
    
    ws = websocket.create_connection(f"ws://{host}:{port}", timeout=5)
    ws.recv()  # Welcome
    
    # Create object
    ws.send(json.dumps({
        "type": "request",
        "id": 1,
        "method": "create_object",
        "params": {"type": "cube", "name": "MatTestCube"}
    }))
    ws.recv()
    
    # Apply material
    ws.send(json.dumps({
        "type": "request",
        "id": 2,
        "method": "set_material",
        "params": {
            "object_name": "MatTestCube",
            "material_name": "TestMaterial",
            "color": [1, 0, 0],
            "metallic": 0.5,
            "roughness": 0.5
        }
    }))
    response = json.loads(ws.recv())
    
    if response.get("type") == "response" and response.get("result", {}).get("success"):
        print("✓ Material application successful")
        ws.close()
        return True
    else:
        print(f"✗ Material application failed: {response}")
        ws.close()
        return False


def run_all_tests(host="localhost", port=8765):
    """Run all tests."""
    print("="*50)
    print("Blender MCP Server Tests")
    print("="*50)
    print()
    
    tests = [
        ("Connection", test_connection),
        ("Ping", test_ping),
        ("Create Object", test_create_object),
        ("Scene Info", test_get_scene_info),
        ("Modify Object", test_modify_object),
        ("Materials", test_materials),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func(host, port)
            results.append((name, success))
        except ConnectionRefusedError:
            print(f"✗ {name}: Connection refused")
            print("\nMake sure the server is running:")
            print("  blender --background --python server/websocket_server.py")
            return False
        except Exception as e:
            print(f"✗ {name}: {e}")
            results.append((name, False))
        print()
    
    # Summary
    print("="*50)
    print("Test Summary")
    print("="*50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    print("="*50)
    
    return passed == total


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Blender MCP Server")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8765, help="Server port")
    parser.add_argument("--test", choices=["all", "connection", "ping", "create", "scene", "modify", "material"],
                       default="all", help="Specific test to run")
    
    args = parser.parse_args()
    
    if args.test == "all":
        success = run_all_tests(args.host, args.port)
    else:
        test_map = {
            "connection": test_connection,
            "ping": test_ping,
            "create": test_create_object,
            "scene": test_get_scene_info,
            "modify": test_modify_object,
            "material": test_materials,
        }
        try:
            success = test_map[args.test](args.host, args.port)
        except ConnectionRefusedError:
            print("Connection refused. Is the server running?")
            success = False
    
    sys.exit(0 if success else 1)
