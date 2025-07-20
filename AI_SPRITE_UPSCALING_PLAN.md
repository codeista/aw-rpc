# AI Sprite Upscaling Plan

## Date: 2025-07-20

## Current Assets
- **Unit sprites**: 16x16 pixels in `/static/img/units_sprite_sheet_v2.png`
- **Terrain tiles**: 16x16 pixels in tileset images
- **Style**: Pixel art from Advance Wars

## AI Upscaling Options

### 1. Pixel Art Specific AI (BEST)
**Tools:**
- **ESRGAN with Pixel Art models**
- **Real-ESRGAN** with anime/pixel models
- **Pixelator** - Designed for pixel art
- **xBRZ** - Algorithm specifically for pixel art

**Pros:**
- Maintains pixel art style
- Sharp edges, no blur
- 2x, 3x, 4x scaling options

**Process:**
```python
# Example with Real-ESRGAN
from realesrgan import RealESRGAN

model = RealESRGAN('realesrgan-x4plus-anime')  # Good for pixel art
upscaled = model.predict(sprite_image, scale=3)
```

### 2. Traditional Nearest Neighbor + AI Enhancement
**Approach:**
1. First scale 3x with nearest neighbor (keeps pixels sharp)
2. Then use AI to add detail and smooth edges
3. Finally quantize back to limited color palette

**Tools:**
- PIL/Pillow for nearest neighbor
- Stable Diffusion img2img for enhancement
- ImageMagick for color quantization

### 3. Stable Diffusion Img2Img Upscaling
**Process:**
```python
# Prompt for SD
prompt = "pixel art sprite, advance wars style, military unit, \
          crisp pixels, limited color palette, game asset"
negative = "blurry, smooth, realistic, photograph"

# Low denoising strength to preserve original
image = pipeline(prompt, image=sprite, strength=0.3, 
                guidance_scale=7.5)
```

## Recommended Approach

### Step 1: Extract Individual Sprites
```python
from PIL import Image
import os

def extract_sprites(sheet_path, sprite_size=16):
    sheet = Image.open(sheet_path)
    sprites = []
    
    for y in range(0, sheet.height, sprite_size):
        for x in range(0, sheet.width, sprite_size):
            sprite = sheet.crop((x, y, x+sprite_size, y+sprite_size))
            if sprite.getbbox():  # Skip empty sprites
                sprites.append(sprite)
    
    return sprites
```

### Step 2: Upscale with ESRGAN
```bash
# Install
pip install basicsr realesrgan

# Run upscaling
python inference_realesrgan.py -n RealESRGAN_x4plus_anime_6B \
    -i input_sprites/ -o output_sprites/ --scale 3
```

### Step 3: Clean Up & Validate
```python
def clean_upscaled_sprite(image, target_size=48):
    # Ensure exact size
    image = image.resize((target_size, target_size), Image.NEAREST)
    
    # Reduce colors to match original palette
    image = image.quantize(colors=16)
    
    # Ensure transparent background
    image = image.convert("RGBA")
    
    return image
```

### Step 4: Reassemble Sprite Sheet
```python
def create_upscaled_sheet(sprites, columns=32):
    sprite_size = 48  # 3x original
    rows = (len(sprites) + columns - 1) // columns
    
    sheet = Image.new('RGBA', 
        (columns * sprite_size, rows * sprite_size), 
        (0, 0, 0, 0))
    
    for i, sprite in enumerate(sprites):
        x = (i % columns) * sprite_size
        y = (i // columns) * sprite_size
        sheet.paste(sprite, (x, y))
    
    return sheet
```

## Quick Alternative: Online Tools

### 1. waifu2x (Free, Online)
- Visit: https://waifu2x.udp.jp/
- Upload sprite sheet
- Style: Artwork
- Noise Reduction: None
- Scale: 3x

### 2. AI Image Enlarger
- https://imglarger.com/
- Works well for pixel art
- Free tier available

### 3. Pixelator.io
- Specifically for pixel art
- Maintains style better

## Implementation Plan

1. **Test Phase (1 hour)**
   - Extract a few unit sprites
   - Try different AI models
   - Compare results

2. **Full Processing (2-3 hours)**
   - Process all sprite sheets
   - Validate quality
   - Fix any issues

3. **Integration (2-3 hours)**
   - Update sprite coordinates
   - Modify rendering code
   - Test in game

## Expected Results
- 48x48 sprites that maintain pixel art style
- Sharper details than simple nearest neighbor
- Proper edge handling
- Consistent art style

## Next Steps
1. Which sprites to prioritize? (units, terrain, or both?)
2. Do you want me to create the extraction script?
3. Should we test with a few sprites first?

The AI approach can give us much better results than simple scaling while maintaining the Advance Wars aesthetic.