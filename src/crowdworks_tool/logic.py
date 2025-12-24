import requests
from bs4 import BeautifulSoup
import json
import time
import random

def fetch_yahoo_ranking(query):
    """
    Searches for the query on Yahoo Japan (smartphone version) and returns the URL of the 1st organic result.
    Returns:
        url (str): The URL of the 1st organic result, or None if not found.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
    }
    url = f"https://search.yahoo.co.jp/search?p={query}&ei=UTF-8"

    print(f"Searching for: {query}")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Strategy 1: JSON Hydration (Next.js)
        next_data = soup.find('script', id='__NEXT_DATA__', type='application/json')
        if next_data:
            try:
                data = json.loads(next_data.string)
                page_data = data.get('props', {}).get('pageProps', {}).get('initialProps', {}).get('pageData', {})
                algos = page_data.get('algos', [])

                if algos and len(algos) > 0:
                    first_result = algos[0]
                    return first_result.get('url')
            except Exception as e:
                print(f"JSON parsing failed: {e}")

        # Strategy 2: HTML Fallback
        # Look for organic search results in the DOM
        # Yahoo Mobile often uses classes like .sw-CardBase for cards.
        # Inside, we look for links that are not ads.

        # Note: Class names are often minified or changing, but some structural semantics might remain.
        # Inspecting the provided HTML dump:
        # <div class="sw-CardBase"><div class="sw-Card Unit Unit--south"><section>...
        # Organic results often have `class="sw-CardBase"`
        # The link is inside `a` tag.

        cards = soup.find_all('div', class_='sw-CardBase')
        for card in cards:
            # Filter out ads if possible. Ads might have specific classes or be in different containers.
            # In the dump, organic results are in 'algos' in JSON, which maps to cards.
            # Let's try to find the first anchor tag in a card that looks like a result title.

            # This is a bit heuristic without live inspection of ad classes.
            # Usually ads are marked with "スポンサー" text or similar structure.

            # Simple fallback: Find first link in the card
            link = card.find('a', href=True)
            if link:
                href = link['href']
                # Yahoo often wraps links. Decode if necessary, or just return href if it's direct.
                # In the JSON dump, URLs are direct. In HTML, they might be tracking links.
                # Example: /xts/FOR=...
                # If it starts with /xts/ or /search, it might be internal or tracking.
                # But typically organic results in JSON `url` field are the real ones.

                # If we are here, JSON failed.
                # Let's try to find a link that looks like an external URL.
                if href.startswith('http'):
                     return href

    except Exception as e:
        print(f"Request failed: {e}")
        return None

    return None

def random_sleep(min_seconds=2, max_seconds=5):
    time.sleep(random.uniform(min_seconds, max_seconds))
