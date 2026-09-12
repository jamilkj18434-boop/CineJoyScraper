import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

async def get_stream_url(page, movie_url):
    """Navigates to a movie page and looks for the embedded stream source."""
    try:
        print(f"Resolving video stream for: {movie_url}")
        await page.goto(movie_url, wait_until="networkidle", timeout=15000)
        await page.wait_for_timeout(2000)
        
        # Look for iframe player sources or m3u8 requests
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Check iframe src tags
        iframe = soup.find('iframe', src=True)
        if iframe and 'http' in iframe['src']:
            return iframe['src']
            
        return movie_url  # Fallback to page URL if stream embed is heavily obfuscated
    except Exception as e:
        print(f"Failed to fetch video stream: {e}")
        return movie_url

async def main():
    base_url = "https://cinejoy.to"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        # Step 1: Get movie links
        await page.goto(f"{base_url}/", wait_until="networkidle", timeout=30000)
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        movie_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            title = a.get_text(strip=True)
            if title and '/movie/' in href:
                full_url = href if href.startswith('http') else f"{base_url}{href}"
                movie_links.append((title, full_url))

        # Limit to top 10 movies for speed and execution limits
        playlist_lines = ["#EXTM3U\n"]
        for title, page_url in movie_links[:10]:
            stream_url = await get_stream_url(page, page_url)
            entry = f'#EXTINF:-1 tvg-name="{title}" group-title="Movies",{title}\n{stream_url}\n'
            playlist_lines.append(entry)

        with open("my_cinema.m3u", "w", encoding="utf-8") as f:
            f.writelines(playlist_lines)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
