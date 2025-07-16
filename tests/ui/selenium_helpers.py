"""
Selenium Helper Utilities for AW-RPC UI Testing

This module provides helper functions for:
- Visual verification using image analysis
- Canvas coordinate calculations
- Color detection for highlights
- Game state validation
"""

import numpy as np
from PIL import Image, ImageDraw
from typing import List, Tuple, Dict, Optional
import cv2
import io


class ColorDetector:
    """Detect specific colors in screenshots for highlight verification"""
    
    # Define highlight colors (BGR format for OpenCV)
    COLORS = {
        'movement': {
            'rgb': (255, 248, 220),  # Light yellow/gold
            'bgr': (220, 248, 255),
            'range_lower': np.array([200, 228, 235]),
            'range_upper': np.array([240, 255, 255])
        },
        'attack': {
            'rgb': (255, 0, 0),  # Red
            'bgr': (0, 0, 255),
            'range_lower': np.array([0, 0, 200]),
            'range_upper': np.array([50, 50, 255])
        },
        'transport_load': {
            'rgb': (76, 175, 80),  # Green
            'bgr': (80, 175, 76),
            'range_lower': np.array([60, 155, 56]),
            'range_upper': np.array([100, 195, 96])
        },
        'transport_unload': {
            'rgb': (33, 150, 243),  # Blue
            'bgr': (243, 150, 33),
            'range_lower': np.array([223, 130, 13]),
            'range_upper': np.array([255, 170, 53])
        }
    }
    
    @staticmethod
    def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
        """Convert PIL Image to OpenCV format"""
        # Convert PIL to numpy array
        numpy_image = np.array(pil_image)
        
        # PIL uses RGB, OpenCV uses BGR
        if len(numpy_image.shape) == 3:
            return cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)
        return numpy_image
    
    @classmethod
    def find_highlights(cls, image: Image.Image, highlight_type: str) -> List[Tuple[int, int, int, int]]:
        """
        Find all highlight regions of a specific type
        Returns list of (x, y, width, height) tuples
        """
        if highlight_type not in cls.COLORS:
            raise ValueError(f"Unknown highlight type: {highlight_type}")
        
        # Convert to OpenCV format
        cv_image = cls.pil_to_cv2(image)
        
        # Get color range for this highlight type
        color_info = cls.COLORS[highlight_type]
        lower = color_info['range_lower']
        upper = color_info['range_upper']
        
        # Create mask for the color range
        mask = cv2.inRange(cv_image, lower, upper)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Get bounding rectangles
        rectangles = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            # Filter out very small regions (noise)
            if w > 5 and h > 5:
                rectangles.append((x, y, w, h))
        
        return rectangles
    
    @classmethod
    def count_highlight_tiles(cls, image: Image.Image, highlight_type: str, tile_size: int = 16) -> int:
        """Count the number of highlighted tiles"""
        rectangles = cls.find_highlights(image, highlight_type)
        
        # Group rectangles into tiles
        tiles = set()
        for x, y, w, h in rectangles:
            # Calculate which tile(s) this rectangle covers
            tile_x = x // tile_size
            tile_y = (y - 16) // tile_size  # Account for scene Y offset
            tiles.add((tile_x, tile_y))
        
        return len(tiles)
    
    @classmethod
    def get_highlight_positions(cls, image: Image.Image, highlight_type: str, tile_size: int = 16) -> List[Tuple[int, int]]:
        """Get tile positions of all highlights"""
        rectangles = cls.find_highlights(image, highlight_type)
        
        tiles = set()
        for x, y, w, h in rectangles:
            tile_x = x // tile_size
            tile_y = (y - 16) // tile_size  # Account for scene Y offset
            tiles.add((tile_x, tile_y))
        
        return sorted(list(tiles))
    
    @classmethod
    def draw_detection_overlay(cls, image: Image.Image, highlight_type: str) -> Image.Image:
        """Draw overlay showing detected highlights (for debugging)"""
        rectangles = cls.find_highlights(image, highlight_type)
        
        # Create a copy to draw on
        result = image.copy()
        draw = ImageDraw.Draw(result)
        
        # Draw rectangles
        color = cls.COLORS[highlight_type]['rgb']
        for x, y, w, h in rectangles:
            draw.rectangle([x, y, x + w, y + h], outline=color, width=2)
        
        return result


class CoordinateHelper:
    """Helper for coordinate calculations and conversions"""
    
    @staticmethod
    def tile_to_canvas(tile_x: int, tile_y: int, tile_size: int = 16) -> Tuple[int, int]:
        """Convert tile coordinates to canvas pixel coordinates"""
        canvas_x = tile_x * tile_size + (tile_size // 2)
        canvas_y = tile_y * tile_size + (tile_size // 2) + 16  # Scene Y offset
        return canvas_x, canvas_y
    
    @staticmethod
    def canvas_to_tile(canvas_x: int, canvas_y: int, tile_size: int = 16) -> Tuple[int, int]:
        """Convert canvas pixel coordinates to tile coordinates"""
        tile_x = canvas_x // tile_size
        tile_y = (canvas_y - 16) // tile_size  # Account for scene Y offset
        return tile_x, tile_y
    
    @staticmethod
    def get_tile_bounds(tile_x: int, tile_y: int, tile_size: int = 16) -> Tuple[int, int, int, int]:
        """Get pixel bounds of a tile (x1, y1, x2, y2)"""
        x1 = tile_x * tile_size
        y1 = tile_y * tile_size + 16  # Scene Y offset
        x2 = x1 + tile_size
        y2 = y1 + tile_size
        return x1, y1, x2, y2


class GameStateValidator:
    """Validate game state changes"""
    
    @staticmethod
    def validate_unit_moved(
        initial_state: Dict, 
        final_state: Dict, 
        from_pos: Tuple[int, int], 
        to_pos: Tuple[int, int]
    ) -> bool:
        """Validate that a unit moved from one position to another"""
        # Check initial position had a unit
        initial_units = initial_state.get('units', [])
        from_unit = next((u for u in initial_units if u['x'] == from_pos[0] and u['y'] == from_pos[1]), None)
        
        if not from_unit:
            return False
        
        # Check final position has the unit
        final_units = final_state.get('units', [])
        to_unit = next((u for u in final_units if u['x'] == to_pos[0] and u['y'] == to_pos[1]), None)
        
        if not to_unit:
            return False
        
        # Verify it's the same unit type
        return from_unit['unit_type'] == to_unit['unit_type']
    
    @staticmethod
    def validate_unit_attacked(
        initial_state: Dict,
        final_state: Dict,
        target_pos: Tuple[int, int]
    ) -> bool:
        """Validate that a unit was attacked (HP reduced or destroyed)"""
        # Find target unit in initial state
        initial_units = initial_state.get('units', [])
        initial_target = next((u for u in initial_units if u['x'] == target_pos[0] and u['y'] == target_pos[1]), None)
        
        if not initial_target:
            return False
        
        # Find target unit in final state
        final_units = final_state.get('units', [])
        final_target = next((u for u in final_units if u['x'] == target_pos[0] and u['y'] == target_pos[1]), None)
        
        # Unit destroyed
        if not final_target:
            return True
        
        # Unit damaged
        return final_target.get('hp', 100) < initial_target.get('hp', 100)
    
    @staticmethod
    def validate_highlights_cleared(game_state: Dict) -> bool:
        """Validate that all highlights are cleared"""
        return (game_state.get('movementHighlights', 0) == 0 and
                game_state.get('attackHighlights', 0) == 0 and
                game_state.get('transportHighlights', 0) == 0)


class VisualDebugger:
    """Helper for visual debugging and test development"""
    
    @staticmethod
    def create_debug_image(
        canvas_image: Image.Image,
        highlights: List[Tuple[int, int]],
        highlight_color: Tuple[int, int, int] = (255, 0, 0),
        tile_size: int = 16
    ) -> Image.Image:
        """Create a debug image with highlighted tiles marked"""
        result = canvas_image.copy()
        draw = ImageDraw.Draw(result)
        
        for tile_x, tile_y in highlights:
            x1, y1, x2, y2 = CoordinateHelper.get_tile_bounds(tile_x, tile_y, tile_size)
            draw.rectangle([x1, y1, x2, y2], outline=highlight_color, width=2)
            
            # Draw tile coordinates
            draw.text((x1 + 2, y1 + 2), f"{tile_x},{tile_y}", fill=highlight_color)
        
        return result
    
    @staticmethod
    def save_debug_comparison(
        before_image: Image.Image,
        after_image: Image.Image,
        filename: str,
        output_dir: str = "/home/box/Documents/aw-rpc/tests/ui/debug"
    ):
        """Save before/after comparison for debugging"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Create side-by-side comparison
        width = before_image.width + after_image.width + 20
        height = max(before_image.height, after_image.height)
        
        comparison = Image.new('RGB', (width, height), color='white')
        comparison.paste(before_image, (0, 0))
        comparison.paste(after_image, (before_image.width + 20, 0))
        
        # Add labels
        draw = ImageDraw.Draw(comparison)
        draw.text((10, 10), "BEFORE", fill='red')
        draw.text((before_image.width + 30, 10), "AFTER", fill='green')
        
        filepath = os.path.join(output_dir, f"{filename}.png")
        comparison.save(filepath)
        return filepath


class TestDataHelper:
    """Helper for setting up specific test scenarios"""
    
    @staticmethod
    def find_units_near_each_other(units: List[Dict], max_distance: int = 3) -> Optional[Tuple[Dict, Dict]]:
        """Find two units that are near each other (for combat testing)"""
        for i, unit1 in enumerate(units):
            for unit2 in units[i+1:]:
                if unit1['army'] != unit2['army']:  # Different armies
                    distance = abs(unit1['x'] - unit2['x']) + abs(unit1['y'] - unit2['y'])
                    if distance <= max_distance:
                        return unit1, unit2
        return None
    
    @staticmethod
    def find_transport_and_cargo(units: List[Dict]) -> Optional[Tuple[Dict, Dict]]:
        """Find a transport and a compatible cargo unit"""
        transports = ['APC', 'LANDER', 'TCOPTER', 'BLACKBOAT', 'CRUISER', 'CARRIER']
        infantry_types = ['INFANTRY', 'MECH']
        
        for unit in units:
            if unit['unit_type'] in transports:
                # Find compatible cargo
                for cargo in units:
                    if cargo['army'] == unit['army']:  # Same army
                        if unit['unit_type'] in ['APC', 'TCOPTER', 'BLACKBOAT'] and cargo['unit_type'] in infantry_types:
                            return unit, cargo
                        elif unit['unit_type'] == 'LANDER' and cargo['unit_type'] not in ['FIGHTER', 'BOMBER', 'BCOPTER', 'TCOPTER']:
                            return unit, cargo
        return None
    
    @staticmethod
    def calculate_movement_range(unit_type: str, movement: int, terrain_map: List[List[str]] = None) -> List[Tuple[int, int]]:
        """Calculate expected movement range for a unit (simplified)"""
        # This is a simplified calculation - real game uses Dijkstra with terrain costs
        # For testing, we can use Manhattan distance
        moves = []
        for dx in range(-movement, movement + 1):
            for dy in range(-movement, movement + 1):
                if abs(dx) + abs(dy) <= movement:
                    moves.append((dx, dy))
        return moves