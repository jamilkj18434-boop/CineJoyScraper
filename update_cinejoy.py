import requests
from bs4 import BeautifulSoup
from datetime import datetime

url = "https://cinejoy.to/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    playlist_lines = ["#EXTM3U\n"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        title = a_tag.get_text(strip=True)
        
        if title and ('/movie/' in href or '/tv/' in href or '/show/' in href):
            full_url = href if href.startswith('http') else f"https://cinejoy.to{href}"
            line = f'#EXTINF:-1 group-title="CineJoy ({now})",{title}\n{full_url}\n'
            playlist_lines.append(line)

    with open("my_cinema.m3u", "w", encoding="utf-8") as f:
        f.writelines(playlist_lines)

    print(f"Done! Scraped {len(playlist_lines) - 1} entries into my_cinema.m3u")

except Exception as e:
    print(f"Error fetching website: {e}")
