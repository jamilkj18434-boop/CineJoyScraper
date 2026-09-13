import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from datetime import datetime

async def extract_m3u8_stream(context, page_url):
    stream_url = None
    page = await context.new_page()
    
    def handle_response(response):
        nonlocal stream_url
        url = response.url
        if ".m3u8" in url and ("index" in url or "master" in url or "m3u8" in url):
            stream_url = url

    page.on("response", handle_response)

    try:
        print(f"Resolving stream for: {page_url}")
        await page.goto(page_url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(3000)
        
        frames = page.frames
        for frame in frames:
            if "embed" in frame.url or "player" in frame.url or "vidsrc" in frame.url:
                await frame.evaluate("() => { document.querySelector('video')?.play(); }")
                
        await page.wait_for_timeout(2000)
    except Exception as e:
        print(f"Stream resolution error on {page_url}: {e}")
    finally:
        await page.close()

    return stream_url

async def main():
    base_url = "https://cinejoy.to"
    referer = "https://cinejoy.to/"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()

        print("Scraping movie list...")
        await page.goto(f"{base_url}/", wait_until="domcontentloaded", timeout=25000)
        await page.wait_for_timeout(3000)
        
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        movie_items = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            title = a.get_text(strip=True)
            if title and '/movie/' in href and len(title) > 2:
                full_url = href if href.startswith('http') else f"{base_url}{href}"
                movie_items.append((title, full_url))

        movie_items = list(dict.fromkeys(movie_items))[:5]

        scraped_streams = {}
        for title, page_url in movie_items:
            m3u8_link = await extract_m3u8_stream(context, page_url)
            if m3u8_link:
                scraped_streams[title] = m3u8_link
                print(f"Found Stream: {title}")
            else:
                print(f"Could not intercept stream for: {title}")

        await browser.close()

    if len(scraped_streams) > 0:
        playlist_lines = ["#EXTM3U\n"]
        now = datetime.now().strftime("%Y-%m-%d")
        
        for title, stream_link in scraped_streams.items():
            formatted_stream_url = f"{stream_link}|Referer={referer}&User-Agent={user_agent}"

            entry = (
                f'#EXTINF:-1 tvg-name="{title}" group-title="CineJoy ({now})",{title}\n'
                f'#EXTHTTP:{{"http-header-fields":{{"Referer":"{referer}","User-Agent":"{user_agent}"}}}}\n'
                f'{formatted_stream_url}\n'
            )
            playlist_lines.append(entry)

        with open("my_cinema.m3u", "w", encoding="utf-8") as f:
            f.writelines(playlist_lines)
        print(f"SUCCESS: Wrote {len(scraped_streams)} Televiso-formatted entries.")
    else:
        print("WARNING: No streams intercepted. Aborting write to prevent file corruption.")

if __name__ == "__main__":
    asyncio.run(main())
