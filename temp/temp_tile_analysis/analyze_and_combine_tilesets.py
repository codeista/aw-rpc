#!/usr/bin/env python3
"""
Tool to analyze, compare, and combine tilesets for Advance Wars RPC.
This tool will:
1. Extract and compare tiles from both sprite sheets
2. Create a combined optimized tileset using the best tiles
3. Generate mapping data for the rendering system
"""

import os
import json
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from collections import defaultdict

class TilesetAnalyzer:
    def __init__(self):
        self.old_tileset_path = 'static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png'
        self.new_tileset_path = 'static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png'
        self.tile_size = 16
        
        # Known tile positions in the old tileset (from render_legacy.js)
        self.old_tileset_center = (445 // 2, 1163 // 2)
        
        # Tile type definitions
        self.tile_categories = {
            'terrain': ['PLAIN', 'WOOD', 'MOUNTAIN', 'ROAD', 'BRIDGE', 'SEA', 'SHOAL', 'REEF', 'RIVER'],
            'properties': ['CITY', 'FACTORY', 'AIRPORT', 'PORT', 'HQ'],
            'special': ['SILO', 'SILO_EMPTY', 'PIPE', 'PIPESEAM', 'RADAR', 'COMTOWER']
        }
        
    def load_tilesets(self):
        """Load both tilesets"""
        print("Loading tilesets...")
        self.old_tileset = Image.open(self.old_tileset_path)
        self.new_tileset = Image.open(self.new_tileset_path)
        
        print(f"Old tileset: {self.old_tileset.size} - Mode: {self.old_tileset.mode}")
        print(f"New tileset: {self.new_tileset.size} - Mode: {self.new_tileset.mode}")
        
        # Convert to RGBA for consistent handling
        if self.old_tileset.mode != 'RGBA':
            self.old_tileset = self.old_tileset.convert('RGBA')
        if self.new_tileset.mode != 'RGBA':
            self.new_tileset = self.new_tileset.convert('RGBA')
    
    def extract_tile_grid(self, image, start_x=0, start_y=0, cols=10, rows=10):
        """Extract a grid of tiles from an image"""
        tiles = []
        for row in range(rows):
            for col in range(cols):
                x = start_x + col * self.tile_size
                y = start_y + row * self.tile_size
                
                if x + self.tile_size <= image.width and y + self.tile_size <= image.height:
                    tile = image.crop((x, y, x + self.tile_size, y + self.tile_size))
                    tiles.append({
                        'image': tile,
                        'position': (x, y),
                        'grid': (col, row)
                    })
        return tiles
    
    def analyze_new_tileset_regions(self):
        """Analyze and identify regions in the new tileset"""
        print("\nAnalyzing new tileset regions...")
        
        # The new tileset appears to have labeled sections
        # Let's identify key regions based on visual inspection
        regions = {
            'roads': {'x': 0, 'y': 0, 'width': 320, 'height': 80},
            'pipes': {'x': 0, 'y': 80, 'width': 320, 'height': 80},
            'terrain': {'x': 0, 'y': 160, 'width': 480, 'height': 160},
            'buildings_red': {'x': 0, 'y': 320, 'width': 240, 'height': 64},
            'buildings_blue': {'x': 240, 'y': 320, 'width': 240, 'height': 64},
            'buildings_green': {'x': 480, 'y': 320, 'width': 240, 'height': 64},
            'buildings_yellow': {'x': 720, 'y': 320, 'width': 240, 'height': 64},
            'buildings_grey': {'x': 960, 'y': 320, 'width': 240, 'height': 64},
            'special_buildings': {'x': 0, 'y': 400, 'width': 1200, 'height': 200}
        }
        
        return regions
    
    def compare_tile_quality(self, tile1, tile2):
        """Compare two tiles and return quality metrics"""
        # Convert to numpy arrays
        arr1 = np.array(tile1)
        arr2 = np.array(tile2)
        
        # Calculate metrics
        metrics = {
            'color_count_1': len(np.unique(arr1.reshape(-1, arr1.shape[2]), axis=0)),
            'color_count_2': len(np.unique(arr2.reshape(-1, arr2.shape[2]), axis=0)),
            'has_transparency_1': np.any(arr1[:, :, 3] < 255),
            'has_transparency_2': np.any(arr2[:, :, 3] < 255),
            'mean_alpha_1': np.mean(arr1[:, :, 3]),
            'mean_alpha_2': np.mean(arr2[:, :, 3])
        }
        
        return metrics
    
    def create_comparison_sheet(self):
        """Create a visual comparison sheet"""
        print("\nCreating comparison sheet...")
        
        # Create a large canvas for comparison
        canvas_width = 1600
        canvas_height = 1200
        canvas = Image.new('RGBA', (canvas_width, canvas_height), (44, 62, 80, 255))
        draw = ImageDraw.Draw(canvas)
        
        # Try to load a font (fallback to default if not available)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        except:
            font = ImageFont.load_default()
            title_font = font
        
        # Title
        draw.text((10, 10), "Tileset Comparison - Old vs New", fill=(255, 255, 255), font=title_font)
        
        # Compare buildings
        y_offset = 50
        
        # Extract building tiles from old tileset
        # Cities are around y=104 in the old tileset
        old_city_tiles = []
        for i in range(5):  # 5 armies
            x = self.old_tileset_center[0] - 8
            y = 104 + i * 95  # Approximate spacing between armies
            if y < self.old_tileset.height - 32:
                tile = self.old_tileset.crop((x, y, x + 16, y + 32))  # Cities are 16x32
                old_city_tiles.append(tile)
        
        # Extract building tiles from new tileset
        regions = self.analyze_new_tileset_regions()
        new_building_tiles = []
        
        for army, region_name in [('RED', 'buildings_red'), ('BLUE', 'buildings_blue'), 
                                  ('GREEN', 'buildings_green'), ('YELLOW', 'buildings_yellow'),
                                  ('GREY', 'buildings_grey')]:
            region = regions[region_name]
            # Extract first few building tiles from each army section
            tiles = self.extract_tile_grid(self.new_tileset, region['x'], region['y'], 5, 2)
            new_building_tiles.extend(tiles[:5])  # Take first 5 tiles
        
        # Draw comparison
        x_offset = 20
        draw.text((x_offset, y_offset), "Building Comparison", fill=(255, 255, 255), font=title_font)
        y_offset += 30
        
        for i, army in enumerate(['RED', 'BLUE', 'GREEN', 'YELLOW', 'GREY']):
            draw.text((x_offset, y_offset), f"{army} Army:", fill=(255, 255, 255), font=font)
            
            # Old tileset building
            if i < len(old_city_tiles):
                canvas.paste(old_city_tiles[i], (x_offset + 100, y_offset), old_city_tiles[i])
                draw.text((x_offset + 120, y_offset + 8), "Old", fill=(255, 200, 200), font=font)
            
            # New tileset buildings
            if i * 5 < len(new_building_tiles):
                for j in range(min(5, len(new_building_tiles) - i * 5)):
                    tile_data = new_building_tiles[i * 5 + j]
                    x_pos = x_offset + 200 + j * 20
                    canvas.paste(tile_data['image'], (x_pos, y_offset), tile_data['image'])
                draw.text((x_offset + 200, y_offset + 20), "New", fill=(200, 255, 200), font=font)
            
            y_offset += 40
        
        # Compare terrain tiles
        y_offset += 20
        draw.text((x_offset, y_offset), "Terrain Comparison", fill=(255, 255, 255), font=title_font)
        y_offset += 30
        
        # Extract terrain from new tileset
        terrain_region = regions['terrain']
        terrain_tiles = self.extract_tile_grid(self.new_tileset, 
                                             terrain_region['x'], 
                                             terrain_region['y'], 
                                             20, 5)
        
        # Display terrain samples
        for i, tile_data in enumerate(terrain_tiles[:40]):  # Show first 40 tiles
            x_pos = x_offset + (i % 20) * 18
            y_pos = y_offset + (i // 20) * 18
            canvas.paste(tile_data['image'], (x_pos, y_pos), tile_data['image'])
        
        # Save comparison sheet
        canvas.save('static/img/tileset_comparison.png')
        print("Saved comparison sheet to static/img/tileset_comparison.png")
        
        return canvas
    
    def create_optimized_tileset(self):
        """Create an optimized combined tileset"""
        print("\nCreating optimized combined tileset...")
        
        # Calculate required size
        # We'll organize tiles in a grid format similar to the new tileset
        tile_cols = 40  # 40 tiles per row
        tile_rows = 30  # Approximate rows needed
        
        canvas_width = tile_cols * self.tile_size
        canvas_height = tile_rows * self.tile_size
        
        combined = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
        
        # Mapping data for the new tileset
        tile_map = {
            'metadata': {
                'version': '1.0',
                'tile_size': self.tile_size,
                'tiles_per_row': tile_cols,
                'source_tilesets': {
                    'old': self.old_tileset_path,
                    'new': self.new_tileset_path
                }
            },
            'tiles': {}
        }
        
        current_row = 0
        current_col = 0
        
        def add_tile(tile_image, tile_name, source='new'):
            nonlocal current_row, current_col
            
            x = current_col * self.tile_size
            y = current_row * self.tile_size
            
            combined.paste(tile_image, (x, y))
            
            tile_map['tiles'][tile_name] = {
                'x': x,
                'y': y,
                'width': tile_image.width,
                'height': tile_image.height,
                'source': source
            }
            
            current_col += tile_image.width // self.tile_size
            if current_col >= tile_cols:
                current_col = 0
                current_row += 1
        
        # Add terrain tiles from new tileset (better quality)
        regions = self.analyze_new_tileset_regions()
        
        # Extract and add terrain tiles
        terrain_tiles = self.extract_tile_grid(self.new_tileset,
                                             regions['terrain']['x'],
                                             regions['terrain']['y'],
                                             30, 10)
        
        for i, tile_data in enumerate(terrain_tiles):
            if not self.is_empty_tile(tile_data['image']):
                add_tile(tile_data['image'], f'terrain_{i}', 'new')
        
        # Add road tiles
        road_tiles = self.extract_tile_grid(self.new_tileset,
                                          regions['roads']['x'],
                                          regions['roads']['y'],
                                          20, 5)
        
        for i, tile_data in enumerate(road_tiles):
            if not self.is_empty_tile(tile_data['image']):
                add_tile(tile_data['image'], f'road_{i}', 'new')
        
        # Add building tiles for each army
        for army in ['red', 'blue', 'green', 'yellow', 'grey']:
            region = regions[f'buildings_{army}']
            building_tiles = self.extract_tile_grid(self.new_tileset,
                                                  region['x'],
                                                  region['y'],
                                                  15, 4)
            
            for i, tile_data in enumerate(building_tiles):
                if not self.is_empty_tile(tile_data['image']):
                    # Buildings are often 16x32, so handle them specially
                    if tile_data['image'].height > self.tile_size:
                        add_tile(tile_data['image'], f'building_{army}_{i}', 'new')
                    else:
                        add_tile(tile_data['image'], f'building_{army}_{i}', 'new')
        
        # Save the combined tileset
        combined = combined.crop((0, 0, canvas_width, (current_row + 1) * self.tile_size))
        combined.save('static/img/tileset_optimized.png', 'PNG')
        
        # Save the tile map
        with open('static/img/tileset_optimized_map.json', 'w') as f:
            json.dump(tile_map, f, indent=2)
        
        print(f"Created optimized tileset: {combined.size}")
        print(f"Total tiles: {len(tile_map['tiles'])}")
        
        return combined, tile_map
    
    def is_empty_tile(self, tile):
        """Check if a tile is empty (fully transparent or single color)"""
        arr = np.array(tile)
        
        # Check if fully transparent
        if np.all(arr[:, :, 3] == 0):
            return True
        
        # Check if single color (no variation)
        unique_colors = len(np.unique(arr.reshape(-1, arr.shape[2]), axis=0))
        return unique_colors <= 1
    
    def create_usage_guide(self):
        """Create a guide for using the dual tileset system"""
        guide = {
            'overview': 'This system uses two tilesets for optimal quality',
            'tilesets': {
                'optimized': {
                    'path': '/static/img/tileset_optimized.png',
                    'use_for': ['buildings', 'roads', 'terrain with better colors'],
                    'format': 'RGBA with full transparency'
                },
                'legacy': {
                    'path': '/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png',
                    'use_for': ['animated water', 'fog effects', 'weather', 'fallback'],
                    'format': 'Indexed color'
                }
            },
            'implementation': {
                'render_function': '''
function getTilesetForTerrain(terrainType) {
    // Use optimized tileset for buildings and roads
    const optimizedTypes = ['CITY', 'FACTORY', 'AIRPORT', 'PORT', 'HQ', 'ROAD', 'BRIDGE'];
    
    if (optimizedTypes.includes(terrainType)) {
        return {
            sheet: '/static/img/tileset_optimized.png',
            map: tilesetOptimizedMap
        };
    }
    
    // Use legacy for animated and special tiles
    return {
        sheet: getSelectedTerrainTileset(),
        map: null  // Use hardcoded positions
    };
}'''
            }
        }
        
        with open('static/img/tileset_usage_guide.json', 'w') as f:
            json.dump(guide, f, indent=2)
        
        print("\nCreated usage guide at static/img/tileset_usage_guide.json")
    
    def run_analysis(self):
        """Run the complete analysis"""
        print("Starting tileset analysis and optimization...")
        
        # Load tilesets
        self.load_tilesets()
        
        # Create comparison sheet
        self.create_comparison_sheet()
        
        # Create optimized tileset
        self.create_optimized_tileset()
        
        # Create usage guide
        self.create_usage_guide()
        
        print("\nAnalysis complete!")
        print("Generated files:")
        print("- static/img/tileset_comparison.png")
        print("- static/img/tileset_optimized.png")
        print("- static/img/tileset_optimized_map.json")
        print("- static/img/tileset_usage_guide.json")


if __name__ == "__main__":
    analyzer = TilesetAnalyzer()
    analyzer.run_analysis()