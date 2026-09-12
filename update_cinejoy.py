import requests
from bs4 import BeautifulSoup
from datetime import datetime

url = "https://cinejoy.to/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers, timeout=15)
    
    # Abort if server is down (503, 502, 404, etc.)
    if response.status_code != 200:
        print(f"Site down (HTTP {response.status_code}). Keeping existing M3U file intact.")
        exit(0)

    soup = BeautifulSoup(response.text, 'html.parser')
    playlist_lines = ["#EXTM3U\n"]
    now = datetime.now().strftime("%Y-%m-%d")

    for a in soup.find_all('a', href=True):
        href = a['href']
        title = a.get_text(strip=True)
        
        if title and len(title) > 2 and ('/movie/' in href or '/tv/' in href or '/show/' in href):
            full_url = href if href.startswith('http') else f"https://cinejoy.to{href}"
            entry = f'#EXTINF:-1 tvg-name="{title}" group-title="CineJoy Movies",{title}\n{full_url}\n'
            playlist_lines.append(entry)

    # Only update file if content was found
    if len(playlist_lines) > 1:
        with open("my_cinema.m3u", "w", encoding="utf-8") as f:
            f.writelines(playlist_lines)
        print(f"Successfully updated with {len(playlist_lines) - 1} entries.")
    else:
        print("No items parsed. Skipping file update.")

except Exception as e:
    print(f"Error: {e}. Keeping current M3U file.")
