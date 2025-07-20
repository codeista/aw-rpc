#!/usr/bin/env python3
"""
Identify road tile types by analyzing which sides connect
"""

from PIL import Image
import json

def identify_road_tiles():
    tileset_path = "static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png"
    tileset = Image.open(tileset_path).convert('RGBA')
    
    # Road tiles start at (12, 19), 16x16 size, 17x17 grid
    start_x = 12
    start_y = 19
    tile_size = 16
    grid_spacing = 17
    
    # Separator color (light blue/grey)
    separator_color = (149, 177, 200)
    
    def is_road_pixel(pixel):
        """Check if pixel is road (greyish) vs grass (not road)"""
        r, g, b, a = pixel
        # Road pixels are greyish - similar R,G,B values
        if a > 0 and abs(r - g) < 30 and abs(g - b) < 30 and r > 100:
            return True
        return False
    
    def check_road_connections(x, y):
        """Check which sides of the tile connect to roads"""
        connections = {
            'north': False,
            'east': False,
            'south': False,
            'west': False
        }
        
        # Sample center pixels on each edge
        # North edge
        for dx in [6, 7, 8, 9]:
            if is_road_pixel(tileset.getpixel((x + dx, y + 1))):
                connections['north'] = True
                break
        
        # East edge
        for dy in [6, 7, 8, 9]:
            if is_road_pixel(tileset.getpixel((x + tile_size - 2, y + dy))):
                connections['east'] = True
                break
        
        # South edge
        for dx in [6, 7, 8, 9]:
            if is_road_pixel(tileset.getpixel((x + dx, y + tile_size - 2))):
                connections['south'] = True
                break
        
        # West edge
        for dy in [6, 7, 8, 9]:
            if is_road_pixel(tileset.getpixel((x + 1, y + dy))):
                connections['west'] = True
                break
        
        return connections
    
    def get_road_type(connections):
        """Determine road type based on connections"""
        n, e, s, w = connections['north'], connections['east'], connections['south'], connections['west']
        
        # Count connections
        count = sum([n, e, s, w])
        
        if count == 2:
            # Straight roads
            if n and s and not e and not w:
                return "ROAD_VERT"
            if e and w and not n and not s:
                return "ROAD_HORT"
            
            # Corner roads
            if n and e and not s and not w:
                return "ROAD_NE"
            if e and s and not n and not w:
                return "ROAD_SE"
            if s and w and not n and not e:
                return "ROAD_SW"
            if w and n and not s and not e:
                return "ROAD_NW"
        
        elif count == 3:
            # T-junctions
            if n and e and s and not w:
                return "NESRoad"  # T-junction open to N,E,S
            if e and s and w and not n:
                return "ESWRoad"  # T-junction open to E,S,W
            if s and w and n and not e:
                return "SWNRoad"  # T-junction open to S,W,N
            if w and n and e and not s:
                return "WNERoad"  # T-junction open to W,N,E
        
        elif count == 4:
            return "CRoad"  # Cross road
        
        elif count == 1:
            # Dead ends
            if n: return "ROAD_END_N"
            if e: return "ROAD_END_E"
            if s: return "ROAD_END_S"
            if w: return "ROAD_END_W"
        
        return "UNKNOWN"
    
    # Analyze road tiles
    road_mapping = []
    
    print("Analyzing road tiles...\n")
    
    for row in range(4):
        for col in range(8):
            x = start_x + col * grid_spacing
            y = start_y + row * grid_spacing
            
            # Check if tile exists
            if x + tile_size > tileset.width or y + tile_size > tileset.height:
                continue
            
            # Check if tile has content
            has_content = False
            for dy in range(tile_size):
                for dx in range(tile_size):
                    pixel = tileset.getpixel((x + dx, y + dy))
                    if pixel[3] > 0 and not (abs(pixel[0] - separator_color[0]) < 15 and 
                                           abs(pixel[1] - separator_color[1]) < 15 and 
                                           abs(pixel[2] - separator_color[2]) < 15):
                        has_content = True
                        break
                if has_content:
                    break
            
            if has_content:
                connections = check_road_connections(x, y)
                road_type = get_road_type(connections)
                
                print(f"Row {row}, Col {col} at ({x}, {y}):")
                print(f"  Connections: N={connections['north']}, E={connections['east']}, S={connections['south']}, W={connections['west']}")
                print(f"  Type: {road_type}\n")
                
                road_mapping.append({
                    "row": row,
                    "col": col,
                    "x": x,
                    "y": y,
                    "type": road_type,
                    "connections": connections
                })
    
    # Save mapping
    with open("road_tiles_identified.json", "w") as f:
        json.dump({"road_tiles": road_mapping}, f, indent=2)
    
    print("Saved to road_tiles_identified.json")

if __name__ == "__main__":
    identify_road_tiles()