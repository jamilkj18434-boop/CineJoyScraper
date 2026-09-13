import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from datetime import datetime

async def extract_m3u8_stream(context, page_url):
    """Navigates to a page, clicks the play player, and extracts master .m3u8 streams."""
    stream_url = None
    page = await context.new_page()
    
    # Intercept network responses and filter out ad/fake manifests
    def handle_response(response):
        nonlocal stream_url
        url = response.url
        # Look for valid video manifest patterns while ignoring common ad servers
        if ".m3u8" in url and not any(ad in url for ad in ["telemetry", "analytics", "popunder", "adsterra"]):
            if "master" in url or "index" in url or "playlist" in url or "m3u8" in url:
                stream_url = url

    page.on("response", handle_response)

    try:
        print(f"Resolving stream for: {page_url}")
        await page.goto(page_url, wait_until="domcontentloaded", timeout=25000)
        await page.wait_for_timeout(3000)
        
        # Click screen center to clear initial overlays/play buttons
        await page.mouse.click(640, 360)
        await page.wait_for_timeout(2000)

        # Iterate all frames and attempt to trigger video playback directly
        for frame in page.frames:
            try:
                await frame.evaluate("""() => {
                    const el = document.querySelector('video') || document.querySelector('.play-btn') || document.querySelector('#player');
                    if (el) el.click();
                }""")
            except Exception:
                pass
                
        await page.wait_for_timeout(4000)
    except Exception as e:
        print(f"Stream resolution error on {page_url}: {e}")
    finally:
        await page.close()

    return stream_url

async def main():
    base_url = "https://cinejoy.to"
    referer = "https://cinejoy.to/"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()

        print("Scraping movie catalog...")
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

        # Process top 5 entries
        movie_items = list(dict.fromkeys(movie_items))[:5]

        scraped_streams = {}
        for title, page_url in movie_items:
            m3u8_link = await extract_m3u8_stream(context, page_url)
            if m3u8_link:
                scraped_streams[title] = m3u8_link
                print(f"SUCCESS: Captured stream for {title}")
            else:
                print(f"FAILED: No valid stream for {title}")

        await browser.close()

    # Write Televiso M3U file
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
        print(f"Saved {len(scraped_streams)} valid streams to my_cinema.m3u.")
    else:
        print("ABORTED: 0 streams intercepted.")

if __name__ == "__main__":
    asyncio.run(main())
