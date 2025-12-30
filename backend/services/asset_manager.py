import os
import aiofiles
import httpx
from typing import Dict, Any, List
from PIL import Image

class AssetManager:
    def __init__(self, base_dir: str = "results"):
        self.base_dir = base_dir

    def create_task_dirs(self, task_id: str):
        path = os.path.join(self.base_dir, task_id)
        subdirs = ["Snapshot", "Brand Assets", "Fonts", "Google Search", "Colors"]
        for d in subdirs:
            os.makedirs(os.path.join(path, d), exist_ok=True)
        return path

    async def save_screenshot(self, task_id: str, screenshot_bytes: bytes, filename: str = "homepage.png"):
        path = os.path.join(self.base_dir, task_id, "Snapshot", filename)
        async with aiofiles.open(path, "wb") as f:
            await f.write(screenshot_bytes)
        return path

    async def save_assets(self, task_id: str, assets: List[Dict[str, str]]):
        paths = []
        async with httpx.AsyncClient() as client:
            for i, asset in enumerate(assets):
                try:
                    url = asset['url']
                    if not url.startswith('http'): continue
                    
                    response = await client.get(url, timeout=10)
                    if response.status_code == 200:
                        ext = url.split('.')[-1].split('?')[0]
                        if len(ext) > 4 or '/' in ext: ext = "png" # fallback
                        
                        filename = f"{asset['type']}_{i}.{ext}"
                        path = os.path.join(self.base_dir, task_id, "Brand Assets", filename)
                        
                        async with aiofiles.open(path, "wb") as f:
                            await f.write(response.content)
                        paths.append(path)
                except Exception as e:
                    print(f"Failed to download asset {asset['url']}: {e}")
        return paths

    async def save_fonts(self, task_id: str, fonts: List[str]):
        path = os.path.join(self.base_dir, task_id, "Fonts", "fonts.txt")
        async with aiofiles.open(path, "w") as f:
            for font in fonts:
                await f.write(f"{font}\n")

    async def save_colors(self, task_id: str, colors: List[str]):
        # Save hex codes text
        text_path = os.path.join(self.base_dir, task_id, "Colors", "colors.txt")
        async with aiofiles.open(text_path, "w") as f:
            for color in colors:
                await f.write(f"{color}\n")
        
        # Create color images
        for i, color in enumerate(colors):
            try:
                # Basic parsing of rgb(r, g, b) or rgba
                # For now, let's just attempt to use Image.new with the color string directly if supported,
                # or parse it. PIL supports 'rgb(x,y,z)'? No, it supports hex or names.
                # We need a converter. 
                # Simplification: User asked for "Find all colors information with Hex code".
                # Scraper returns rgb usually. I should convert rgb to hex.
                pass 
            except Exception:
                pass
                
    def rgb_to_hex(self, rgb_str: str) -> str:
        # Simple regex to parse rgb(r, g, b) or rgba(r, g, b, a)
        import re
        match = re.search(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*[\d\.]+)?\)', rgb_str)
        if match:
            r, g, b = map(int, match.groups())
            return '#{:02x}{:02x}{:02x}'.format(r, g, b)
        if rgb_str.startswith('#'):
            return rgb_str
        return None

    async def save_color_images(self, task_id: str, colors: List[str]):
        paths = []
        for i, color in enumerate(colors):
            hex_color = self.rgb_to_hex(color)
            if not hex_color: continue
            
            try:
                # Remove # for filename
                hex_name = hex_color.replace('#', '')
                path = os.path.join(self.base_dir, task_id, "Colors", f"{hex_name}.png")
                
                img = Image.new('RGB', (50, 50), color=hex_color)
                img.save(path)
                paths.append({"hex": hex_color, "path": path})
            except Exception as e:
                print(f"Could not save color image for {color}: {e}")
        return paths
        return paths

    async def save_css(self, task_id: str, css_list: List[Dict[str, str]]):
        paths = []
        css_dir = os.path.join(self.base_dir, task_id, "CSS")
        os.makedirs(css_dir, exist_ok=True)
        
        async with httpx.AsyncClient() as client:
            for i, asset in enumerate(css_list):
                try:
                    if asset['type'] == 'external_css':
                        url = asset['url']
                        response = await client.get(url, timeout=10)
                        if response.status_code == 200:
                            filename = f"style_{i}.css"
                            path = os.path.join(css_dir, filename)
                            async with aiofiles.open(path, "wb") as f:
                                await f.write(response.content)
                            paths.append(path)
                    elif asset['type'] == 'inline_css':
                        filename = f"inline_{i}.css"
                        path = os.path.join(css_dir, filename)
                        async with aiofiles.open(path, "w") as f:
                            await f.write(asset['content'])
                        paths.append(path)
                except Exception as e:
                    print(f"Failed to save CSS asset: {e}")
        return paths
