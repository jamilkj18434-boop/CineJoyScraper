import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime

# Initialize cloudscraper to simulate a real Chrome browser session
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

url = "https://cinejoy.to/"

try:
    print("Connecting to CineJoy via Cloudscraper...")
    response = scraper.get(url, timeout=20)
    
    if response.status_code != 200:
        print(f"Failed to load site. Status code: {response.status_code}")
        exit(0)

    soup = BeautifulSoup(response.text, 'html.parser')
    playlist_lines = ["#EXTM3U\n"]
    now = datetime.now().strftime("%Y-%m-%d")

    # Parse all anchor links
    for a in soup.find_all('a', href=True):
        href = a['href']
        title = a.get_text(strip=True)
        
        # Check if the title exists and points to a movie/tv route
        if title and len(title) > 2 and any(k in href for k in ['/movie/', '/tv/', '/show/', '/series/']):
            full_url = href if href.startswith('http') else f"https://cinejoy.to{href}"
            entry = f'#EXTINF:-1 tvg-name="{title}" group-title="CineJoy Content",{title}\n{full_url}\n'
            playlist_lines.append(entry)

    if len(playlist_lines) > 1:
        with open("my_cinema.m3u", "w", encoding="utf-8") as f:
            f.writelines(playlist_lines)
        print(f"Success! Updated my_cinema.m3u with {len(playlist_lines) - 1} entries.")
    else:
        print("No media links found on the main page.")

except Exception as e:
        print(f"Error executing scraper: {e}")
