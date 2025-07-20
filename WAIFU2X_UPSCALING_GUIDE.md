# Waifu2x Sprite Upscaling Guide

## Quick Steps for AI Upscaling

### Step 1: Upload Sprites to Waifu2x

1. **Open waifu2x**: https://waifu2x.udp.jp/
2. **Settings to use**:
   - Style: **Artwork** (not Photo)
   - Noise Reduction: **None** (our sprites are clean)
   - Upscaling: **3x**
   - Format: **PNG**

3. **Upload Process**:
   - Since we have 3,000 sprites, you'll need to batch them
   - Waifu2x web version handles one at a time
   - Alternative: Use the batch-capable version at https://waifu2x.booru.pics/

### Step 2: Batch Processing Options

#### Option A: waifu2x-caffe (Windows)
- Download: https://github.com/lltcggie/waifu2x-caffe/releases
- Can process entire folders
- Same quality as web version

#### Option B: waifu2x-ncnn-vulkan (Cross-platform)
```bash
# Install
git clone https://github.com/nihui/waifu2x-ncnn-vulkan.git
cd waifu2x-ncnn-vulkan
mkdir build && cd build
cmake .. && make -j4

# Run batch processing
./waifu2x-ncnn-vulkan -i /home/box/Documents/aw-rpc/temp/sprites_to_upscale -o /home/box/Documents/aw-rpc/temp/sprites_upscaled_ai -n -1 -s 3
```

#### Option C: Online Batch Services
- **waifu2x.booru.pics** - Allows ZIP uploads
- **bigjpg.com** - Free tier allows batches
- **imglarger.com** - Good for pixel art

### Step 3: Quick Python Script for Batch Upload

If you want to automate the web version:

```python
import requests
import os
from pathlib import Path

def upscale_with_waifu2x_api(input_dir, output_dir):
    """Use waifu2x API for batch processing"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    # API endpoint (if available)
    api_url = "https://api.waifu2x.booru.pics/convert"
    
    for sprite_file in Path(input_dir).glob("*.png"):
        with open(sprite_file, 'rb') as f:
            files = {'file': f}
            data = {
                'scale': '3',
                'noise': '-1',
                'style': 'art'
            }
            
            response = requests.post(api_url, files=files, data=data)
            
            if response.status_code == 200:
                output_path = Path(output_dir) / sprite_file.name
                with open(output_path, 'wb') as out:
                    out.write(response.content)
                print(f"Upscaled: {sprite_file.name}")
            else:
                print(f"Failed: {sprite_file.name}")
```

### Step 4: After Upscaling

Once you have the AI-upscaled sprites in `temp/sprites_upscaled_ai/`:

```bash
# Reassemble the sprite sheet
python upscale_sprites.py --reassemble-only
```

This will create: `static/img/units_sprite_sheet_48x48_ai.png`

## Recommended Approach

Given the 3,000 sprites, I recommend:

1. **For testing** (5-10 sprites): Use the web interface manually
2. **For full batch**: Use waifu2x-ncnn-vulkan or upload as ZIP to waifu2x.booru.pics

## Expected Results

- Sprites will be 48x48 pixels (3x original)
- Edges will be smoother but still pixelated
- Colors will be preserved
- Transparency will be maintained

## Time Estimate

- Manual web upload: 5-8 hours (not recommended)
- Batch tool: 30-60 minutes
- ZIP upload: 10-15 minutes

Let me know which approach you'd like to use, or if you want me to create a more automated solution!