import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime
import re

# Set up cloudscraper with full browser headers
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

base_url = "https://cinejoy.to"

# Try multiple listing paths to ensure content is found
target_urls = [
    f"{base_url}/",
    f"{base_url}/movies",
    f"{base_url}/tv-shows",
    f"{base_url}/trending"
]

scraped_items = {}
now = datetime.now().strftime("%Y-%m-%d")

for url in target_urls:
    try:
        print(f"Scraping {url}...")
        response = scraper.get(url, timeout=15)
        
        if response.status_code != 200:
            print(f"Skipping {url} (HTTP Status {response.status_code})")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')

        # Look for any links pointing to movies or TV shows
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            title = a_tag.get_text(strip=True)

            # Fallback to img alt tag if anchor text is blank
            if not title:
                img = a_tag.find('img')
                if img and img.get('alt'):
                    title = img['alt'].strip()

            if title and len(title) > 2 and any(k in href for k in ['/movie/', '/tv/', '/show/', '/series/']):
                full_url = href if href.startswith('http') else f"{base_url}{href}"
                scraped_items[full_url] = title

    except Exception as e:
        print(f"Error checking {url}: {e}")

# Build M3U lines
playlist_lines = ["#EXTM3U\n"]

for link, title in scraped_items.items():
    entry = f'#EXTINF:-1 tvg-name="{title}" group-title="CineJoy ({now})",{title}\n{link}\n'
    playlist_lines.append(entry)

# CRITICAL SAFEGUARD: Never overwrite the file if 0 items were scraped
if len(playlist_lines) > 1:
    with open("my_cinema.m3u", "w", encoding="utf-8") as f:
        f.writelines(playlist_lines)
    print(f"SUCCESS: Wrote {len(playlist_lines) - 1} entries to my_cinema.m3u")
else:
    print("WARNING: 0 items scraped. Existing M3U left untouched to prevent wiping.")
