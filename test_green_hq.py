#!/usr/bin/env python3
"""Test green HQ rendering specifically"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=chrome_options)

try:
    print("🏰 Testing Green HQ rendering...")
    driver.get('http://localhost:5000/test_clean_2x')
    time.sleep(3)
    
    # Create a test with just HQs
    test_result = driver.execute_script("""
        // Clear and test just HQs
        if (window.terrainGroup) {
            window.terrainGroup.remove(...window.terrainGroup.children);
        }
        
        // Test different colored HQs
        const testHQs = [
            {x: 0, y: 0, type: 'RED_BASE_TOWER_1'},
            {x: 1, y: 0, type: 'BLUE_BASE_TOWER_1'},
            {x: 2, y: 0, type: 'GREEN_BASE_TOWER_1'},
            {x: 3, y: 0, type: 'YELLOW_BASE_TOWER_1'},
            {x: 0, y: 1, type: 'PLAIN'}, // Plain under for comparison
            {x: 1, y: 1, type: 'PLAIN'},
            {x: 2, y: 1, type: 'PLAIN'},
            {x: 3, y: 1, type: 'PLAIN'}
        ];
        
        const results = [];
        
        // First render plains
        testHQs.filter(t => t.type === 'PLAIN').forEach(test => {
            const sprite = window.terrainMap[test.type];
            if (sprite) {
                const texture = new Two.Texture('/static/img/sprites_2x/combined/terrain_tileset_2x.png');
                texture.offset = new Two.Vector(
                    256 - (sprite.x + sprite.w/2),
                    208 - (sprite.y + sprite.h/2)
                );
                
                const rect = window.two.makeRectangle(
                    test.x * 32 + 16,
                    test.y * 32 + 16,
                    32, 32
                );
                
                rect.fill = texture;
                rect.noStroke();
                window.terrainGroup.add(rect);
            }
        });
        
        // Then render HQs
        testHQs.filter(t => t.type !== 'PLAIN').forEach(test => {
            const sprite = window.terrainMap[test.type];
            if (!sprite) {
                results.push({...test, error: 'Sprite not found'});
                return;
            }
            
            const texture = new Two.Texture('/static/img/sprites_2x/combined/terrain_tileset_2x.png');
            texture.offset = new Two.Vector(
                256 - (sprite.x + sprite.w/2),
                208 - (sprite.y + sprite.h/2)
            );
            
            // HQs are 32x64
            const rect = window.two.makeRectangle(
                test.x * 32 + 16,
                test.y * 32,  // Adjust Y for double height
                32, 64
            );
            
            rect.fill = texture;
            rect.noStroke();
            window.terrainGroup.add(rect);
            
            results.push({
                ...test,
                sprite: sprite,
                transparency: sprite.transparency || 'unknown'
            });
        });
        
        window.two.update();
        return results;
    """)
    
    print("\nHQs rendered:")
    for result in test_result:
        if 'error' in result:
            print(f"  ❌ {result['type']}: {result['error']}")
        else:
            print(f"  ✅ {result['type']}")
    
    # Take screenshot
    driver.save_screenshot('/tmp/hq_comparison.png')
    print("\n📸 Screenshot saved: /tmp/hq_comparison.png")
    
    # Analyze the green HQ area
    analysis = driver.execute_script("""
        const canvas = document.querySelector('canvas');
        if (!canvas) return {error: 'No canvas'};
        
        const ctx = canvas.getContext('2d');
        
        // Sample the green HQ area (x=2, y=0)
        const hqX = 2 * 32;
        const hqY = 0;
        
        // Get a sample from the center of the green HQ
        const imageData = ctx.getImageData(hqX + 8, hqY + 8, 16, 16);
        const pixels = imageData.data;
        
        // Count color types
        const colors = {};
        let transparentCount = 0;
        
        for (let i = 0; i < pixels.length; i += 4) {
            const r = pixels[i];
            const g = pixels[i+1];
            const b = pixels[i+2];
            const a = pixels[i+3];
            
            if (a === 0) {
                transparentCount++;
            } else {
                const key = `${Math.floor(r/20)*20},${Math.floor(g/20)*20},${Math.floor(b/20)*20}`;
                colors[key] = (colors[key] || 0) + 1;
            }
        }
        
        // Get dominant colors
        const sortedColors = Object.entries(colors)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5);
        
        return {
            transparentPixels: transparentCount,
            totalPixels: 16 * 16,
            dominantColors: sortedColors
        };
    """)
    
    print("\n🎨 Green HQ analysis:")
    print(f"  Transparent pixels: {analysis['transparentPixels']}/{analysis['totalPixels']}")
    print("  Dominant colors:")
    for color, count in analysis['dominantColors']:
        print(f"    RGB({color}): {count} pixels")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    driver.quit()

# Also save individual HQ sprites for visual inspection
import os
os.system('rm -f check_hq_transparency.py test_simple_tiles.py')