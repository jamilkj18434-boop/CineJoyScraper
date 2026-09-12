import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from datetime import datetime

async def main():
    url = "https://cinejoy.to/"
    
    async with async_playwright() as p:
        # Launch headless browser with anti-bot evasion settings
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        
        print(f"Loading {url} via Headless Browser...")
        try:
            # Navigate and wait for JavaScript content to fully render
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)  # Wait 3s for hydration
            
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            playlist_lines = ["#EXTM3U\n"]
            now = datetime.now().strftime("%Y-%m-%d")
            scraped_items = {}

            # Parse rendered anchor tags
            for a in soup.find_all('a', href=True):
                href = a['href']
                title = a.get_text(strip=True)
                
                if not title:
                    img = a.find('img')
                    if img and img.get('alt'):
                        title = img['alt'].strip()

                if title and len(title) > 2 and any(k in href for k in ['/movie/', '/tv/', '/show/', '/series/']):
                    full_url = href if href.startswith('http') else f"https://cinejoy.to{href}"
                    scraped_items[full_url] = title

            for link, title in scraped_items.items():
                entry = f'#EXTINF:-1 tvg-name="{title}" group-title="CineJoy ({now})",{title}\n{link}\n'
                playlist_lines.append(entry)

            # Prevent wiping the M3U if 0 items are extracted
            if len(playlist_lines) > 1:
                with open("my_cinema.m3u", "w", encoding="utf-8") as f:
                    f.writelines(playlist_lines)
                print(f"SUCCESS: Extracted {len(scraped_items)} items into my_cinema.m3u")
            else:
                print("WARNING: JavaScript rendered, but 0 media routes matched.")

        except Exception as e:
            print(f"Browser Execution Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
