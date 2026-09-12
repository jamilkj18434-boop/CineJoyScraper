import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from datetime import datetime

async def main():
    base_url = "https://cinejoy.to"
    target_urls = [
        f"{base_url}/",
        f"{base_url}/movies",
        f"{base_url}/tv-shows"
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        scraped_items = {}

        for url in target_urls:
            print(f"Loading {url}...")
            try:
                await page.goto(url, wait_until="networkidle", timeout=25000)
                await page.wait_for_timeout(2000)
                
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')

                for a in soup.find_all('a', href=True):
                    href = a['href']
                    title = a.get_text(strip=True)
                    
                    if not title:
                        img = a.find('img')
                        if img and img.get('alt'):
                            title = img['alt'].strip()

                    # Validate valid media links only
                    if title and len(title) > 2 and not title.startswith('<'):
                        if any(k in href for k in ['/movie/', '/tv/', '/show/', '/series/']):
                            full_url = href if href.startswith('http') else f"{base_url}{href}"
                            scraped_items[full_url] = title
            except Exception as e:
                print(f"Skipping {url} due to error: {e}")

        await browser.close()

    # STRICT SAFEGUARD: Only overwrite if we actually scraped valid items
    if len(scraped_items) > 0:
        playlist_lines = ["#EXTM3U\n"]
        now = datetime.now().strftime("%Y-%m-%d")
        
        for link, title in scraped_items.items():
            entry = f'#EXTINF:-1 tvg-name="{title}" group-title="CineJoy ({now})",{title}\n{link}\n'
            playlist_lines.append(entry)

        with open("my_cinema.m3u", "w", encoding="utf-8") as f:
            f.writelines(playlist_lines)
        print(f"SUCCESS: Wrote {len(scraped_items)} items to my_cinema.m3u")
    else:
        print("ABORTED: 0 items scraped. Preserving existing M3U file.")

if __name__ == "__main__":
    asyncio.run(main())
