"""
Test Terrain Rendering

Tests that would have caught the terrain rendering bugs:
1. Plains showing as solid green instead of sprite
2. Proper sprite loading and display
"""

import time
import pytest
from PIL import Image
import numpy as np
from selenium.webdriver.common.by import By
from test_base_selenium import BaseSeleniumTest


class TestTerrainRendering(BaseSeleniumTest):
    """Test terrain sprites render correctly"""
    
    def get_canvas_screenshot(self):
        """Get screenshot of just the canvas element"""
        canvas = self.get_canvas()
        
        # Get canvas location and size
        location = canvas.location
        size = canvas.size
        
        # Take full screenshot
        self.driver.save_screenshot('/tmp/full_screenshot.png')
        
        # Crop to just canvas
        image = Image.open('/tmp/full_screenshot.png')
        left = location['x']
        top = location['y']
        right = left + size['width']
        bottom = top + size['height']
        
        canvas_image = image.crop((left, top, right, bottom))
        return canvas_image
    
    def test_plains_not_solid_green(self):
        """Test that plains tiles are not rendered as solid green"""
        # Wait for game to fully load
        time.sleep(1)
        
        # Get canvas screenshot
        canvas_img = self.get_canvas_screenshot()
        
        # Convert to numpy array
        img_array = np.array(canvas_img)
        
        # Check for large areas of solid green (#7CB068)
        # This was the bug - entire background was solid green
        target_green = np.array([124, 176, 104])  # RGB for #7CB068
        
        # Sample several tile positions
        tile_size = 40  # Default tile size
        samples_taken = 0
        solid_green_tiles = 0
        
        for y in range(0, img_array.shape[0] - tile_size, tile_size):
            for x in range(0, img_array.shape[1] - tile_size, tile_size):
                # Get center pixel of tile
                center_x = x + tile_size // 2
                center_y = y + tile_size // 2
                
                if center_y < img_array.shape[0] and center_x < img_array.shape[1]:
                    pixel = img_array[center_y, center_x, :3]  # RGB only
                    
                    # Check if it's the solid green color
                    if np.allclose(pixel, target_green, atol=5):
                        # Check if entire tile is solid green
                        tile_area = img_array[y:y+tile_size, x:x+tile_size, :3]
                        
                        # Calculate how uniform the tile is
                        std_dev = np.std(tile_area.reshape(-1, 3), axis=0)
                        
                        if np.all(std_dev < 10):  # Very uniform color
                            solid_green_tiles += 1
                    
                    samples_taken += 1
        
        # Should not have majority solid green tiles
        solid_ratio = solid_green_tiles / max(samples_taken, 1)
        assert solid_ratio < 0.5, \
            f"Too many solid green tiles: {solid_green_tiles}/{samples_taken} ({solid_ratio:.1%})"
    
    def test_terrain_variety_visible(self):
        """Test that different terrain types are visually distinct"""
        # Wait for game to load
        time.sleep(1)
        
        canvas_img = self.get_canvas_screenshot()
        img_array = np.array(canvas_img)
        
        # Sample colors from different parts of the map
        height, width = img_array.shape[:2]
        
        # Sample 10 random positions
        sample_colors = []
        for _ in range(10):
            x = np.random.randint(10, width - 10)
            y = np.random.randint(10, height - 10)
            
            # Get average color in 5x5 area
            area = img_array[y-2:y+3, x-2:x+3, :3]
            avg_color = np.mean(area.reshape(-1, 3), axis=0)
            sample_colors.append(avg_color)
        
        # Check color variety
        sample_colors = np.array(sample_colors)
        
        # Calculate standard deviation across samples
        color_std = np.std(sample_colors, axis=0)
        
        # Should have some variety in colors (not all the same)
        assert np.any(color_std > 20), \
            f"Terrain lacks color variety. Std devs: R={color_std[0]:.1f}, G={color_std[1]:.1f}, B={color_std[2]:.1f}"
    
    def test_buildings_render_differently(self):
        """Test that buildings (factories, cities) look different from plains"""
        # Wait for game to load
        time.sleep(1)
        
        canvas_img = self.get_canvas_screenshot()
        img_array = np.array(canvas_img)
        
        # Known factory position (0, 0) - top-left
        # Known plain position (5, 5) - somewhere in middle
        tile_size = 40
        
        # Get factory tile area
        factory_area = img_array[0:tile_size, 0:tile_size, :3]
        factory_avg = np.mean(factory_area.reshape(-1, 3), axis=0)
        
        # Get plain tile area (adjust for actual map)
        plain_x = 5 * tile_size
        plain_y = 5 * tile_size
        if plain_y + tile_size <= img_array.shape[0] and plain_x + tile_size <= img_array.shape[1]:
            plain_area = img_array[plain_y:plain_y+tile_size, plain_x:plain_x+tile_size, :3]
            plain_avg = np.mean(plain_area.reshape(-1, 3), axis=0)
            
            # Colors should be different
            color_diff = np.abs(factory_avg - plain_avg)
            total_diff = np.sum(color_diff)
            
            assert total_diff > 30, \
                f"Factory and plain should look different. Diff: {total_diff:.1f}"
    
    def test_sprites_load_without_errors(self):
        """Test that sprite loading doesn't cause console errors"""
        # Check browser console for errors
        logs = self.driver.get_log('browser')
        
        # Filter for sprite/image loading errors
        sprite_errors = []
        for log in logs:
            msg = log.get('message', '').lower()
            if any(word in msg for word in ['sprite', 'image', '404', 'failed to load', 'terrain']):
                if log.get('level') == 'SEVERE':
                    sprite_errors.append(log['message'])
        
        assert len(sprite_errors) == 0, \
            f"Found sprite loading errors: {sprite_errors}"
    
    def test_canvas_not_blank(self):
        """Test that canvas actually renders something"""
        # Wait for game to load
        time.sleep(1)
        
        canvas_img = self.get_canvas_screenshot()
        img_array = np.array(canvas_img)
        
        # Check if canvas is not all one color
        unique_colors = np.unique(img_array.reshape(-1, 3), axis=0)
        
        assert len(unique_colors) > 10, \
            f"Canvas appears blank or uniform. Only {len(unique_colors)} unique colors found"
    
    def test_tile_boundaries_visible(self):
        """Test that individual tiles are distinguishable"""
        # This test would check for tile edges/boundaries
        # by looking for regular patterns in the image
        
        canvas_img = self.get_canvas_screenshot()
        img_array = np.array(canvas_img)
        
        # Convert to grayscale for edge detection
        gray = np.mean(img_array[:, :, :3], axis=2)
        
        # Look for vertical lines at tile boundaries
        tile_size = 40
        edge_strength = []
        
        for x in range(tile_size, gray.shape[1] - 1, tile_size):
            # Calculate difference between adjacent columns
            diff = np.abs(gray[:, x] - gray[:, x-1])
            edge_strength.append(np.mean(diff))
        
        # Should have some visible edges
        avg_edge = np.mean(edge_strength) if edge_strength else 0
        assert avg_edge > 5, \
            f"Tile boundaries not visible. Avg edge strength: {avg_edge:.1f}"