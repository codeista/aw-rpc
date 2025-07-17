#!/usr/bin/env python3
"""Quick test to verify tile rendering is working"""

import requests
import time

def test_tile_rendering():
    base_url = "http://localhost:5000"
    
    # Check if server is running
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Server is running: {response.status_code}")
    except:
        print("❌ Server is not running")
        return
    
    # Test tile optimization page
    try:
        response = requests.get(f"{base_url}/tile_optimization_test")
        if response.status_code == 200:
            print("✅ Tile optimization test page loads")
        else:
            print(f"❌ Tile optimization test page error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing tile optimization test: {e}")
    
    # Check if optimized tileset files are served
    files_to_check = [
        "/static/img/optimized_tileset_transparent.png",
        "/static/img/optimized_tileset_normal.png", 
        "/static/img/optimized_tileset_map.json",
        "/static/js/optimized-tile-renderer.js"
    ]
    
    for file_path in files_to_check:
        try:
            response = requests.get(f"{base_url}{file_path}")
            if response.status_code == 200:
                print(f"✅ {file_path} - OK ({len(response.content)} bytes)")
            else:
                print(f"❌ {file_path} - Error {response.status_code}")
        except Exception as e:
            print(f"❌ {file_path} - Exception: {e}")

if __name__ == "__main__":
    test_tile_rendering()