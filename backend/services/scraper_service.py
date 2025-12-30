import asyncio
from playwright.async_api import async_playwright, Page
from playwright_stealth import Stealth
from typing import Dict, List, Any
import re
from urllib.parse import urljoin

class ScraperService:
    async def analyze_url(self, url: str) -> Dict[str, Any]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox", 
                    "--disable-setuid-sandbox", 
                    "--disable-dev-shm-usage",
                    "--disable-http2"
                ]
            )
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Referer": "https://www.google.com/",
                    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                },
                ignore_https_errors=True
            )
            page = await context.new_page()
            
            # Apply stealth
            await Stealth().apply_stealth_async(page)
            
            try:
                # 1. Navigate
                # 1. Navigate
                try:
                    await page.goto(url, wait_until="commit", timeout=60000)
                except Exception as e:
                    print(f"Navigation warning: {e}")
                
                await asyncio.sleep(15) # More time for complex sites like Myntra/Nykaa
                
                # Check if we at least have a body
                # Use a small retry loop for content because Nykaa/Myntra can be 'navigating' for a while
                content = ""
                for _ in range(3):
                    try:
                        content = await page.content()
                        if content: break
                    except Exception as e:
                        print(f"Content retrieval attempt failed: {e}")
                        await asyncio.sleep(5)
                
                print(f"[{url}] Content length: {len(content)}")
                if content:
                    print(f"[{url}] Content snippet: {content[:200].replace('\n', ' ')}")
                
                if not content or len(content) < 500:
                   raise Exception(f"Page failed to load any meaningful content. Length: {len(content)}")
                
                # 2. Screenshot
                # Scroll to bottom and back to top to trigger any lazy loading
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
                await page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(1)
                
                screenshot_bytes = await page.screenshot(full_page=True)
                
                # 3. Extract Meta Info
                title = await page.title()
                if not title: title = url
                try:
                    description = await page.eval_on_selector(
                        "meta[name='description']", 
                        "el => el.content"
                    )
                except:
                    description = ""
                
                # 4. Extract Brand Assets (Favicons, Logos)
                assets = await self._extract_assets(page, url)
                
                # 5. Extract Fonts
                fonts = await self._extract_fonts(page)
                
                # 6. Extract Colors
                colors = await self._extract_colors(page)
                
                # 7. Extract CSS
                css = await self._extract_css(page)
                
                return {
                    "url": url,
                    "title": title,
                    "description": description,
                    "screenshot": screenshot_bytes,
                    "assets": assets,
                    "fonts": fonts,
                    "colors": colors,
                    "css": css
                }
                
            finally:
                await browser.close()

    async def _extract_assets(self, page: Page, base_url: str) -> List[Dict[str, str]]:
        assets = []
        
        # Favicons
        icons = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll("link[rel*='icon']")).map(el => el.href);
        }""")
        for icon in icons:
            assets.append({"type": "favicon", "url": urljoin(base_url, icon)})
            
        # Logos (Heuristic: images with 'logo' in src, class, or id)
        logos = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll("img, svg")).filter(el => {
                const src = el.src || "";
                const cls = el.className || "";
                const id = el.id || "";
                const alt = el.alt || "";
                return (src.toLowerCase().includes('logo') || 
                        cls.toString().toLowerCase().includes('logo') || 
                        id.toString().toLowerCase().includes('logo') ||
                        alt.toLowerCase().includes('logo'));
            }).map(el => el.src || ""); // Note: handling SVGs without src? For now just src.
        }""")
        for logo in logos:
            if logo:
                assets.append({"type": "logo", "url": urljoin(base_url, logo)})
                
        return assets

    async def _extract_fonts(self, page: Page) -> List[str]:
        # Get computed font-family from body, headings, buttons
        fonts = await page.evaluate("""() => {
            const elements = document.querySelectorAll("h1, h2, h3, h4, h5, h6, button, a, [class*='font'], [id*='font']");
            const fonts = new Set();
            elements.forEach(el => {
                const font = window.getComputedStyle(el).fontFamily;
                if (font) fonts.add(font);
            });
            return Array.from(fonts).slice(0, 10);
        }""")
        return fonts

    async def _extract_colors(self, page: Page) -> List[str]:
        # Extract common colors (backgrounds, text colors of headings/buttons)
        # Also look for CSS variables?
        colors = await page.evaluate("""() => {
            // Target only representative elements to avoid hanging on massive DOMs
            const elements = document.querySelectorAll("h1, h2, h3, button, a, nav, footer, [class*='header'], [class*='brand']");
            const colorCounts = {};
            
            elements.forEach(el => {
                const style = window.getComputedStyle(el);
                const bg = style.backgroundColor;
                const fg = style.color;
                
                [bg, fg].forEach(c => {
                    if (c && c !== 'rgba(0, 0, 0, 0)' && c !== 'transparent' && c !== 'rgba(0,0,0,0)') {
                        colorCounts[c] = (colorCounts[c] || 0) + 1;
                    }
                });
            });
            
            // Sort by frequency
            return Object.entries(colorCounts)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10)
                .map(([c]) => c);
        }""")
        
        # Convert RGB to Hex in Python or JS? JS is fine but let's just return what we got (usually rgb/rgba)
        # We can normalize in Python
        return colors

    async def _extract_css(self, page: Page) -> List[Dict[str, str]]:
        # Extract main external stylesheets and significant inline styles
        css_assets = await page.evaluate("""() => {
            const results = [];
            
            // 1. External Stylesheets
            Array.from(document.querySelectorAll("link[rel='stylesheet']")).forEach(el => {
                if (el.href) results.push({ type: 'external_css', url: el.href });
            });
            
            // 2. Significant Inline Styles (just the first few if many)
            const inlineStyles = Array.from(document.querySelectorAll("style"));
            inlineStyles.slice(0, 3).forEach((el, i) => {
                if (el.textContent && el.textContent.trim().length > 100) {
                    results.push({ 
                        type: 'inline_css', 
                        content: el.textContent.substring(0, 5000) // Caps to avoid huge strings
                    });
                }
            });
            
            return results;
        }""")
        return css_assets
