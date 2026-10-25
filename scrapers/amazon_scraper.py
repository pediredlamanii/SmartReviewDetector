import requests  # pyrefly: ignore [missing-import]
from bs4 import BeautifulSoup  # pyrefly: ignore [missing-import]
import re
import json

def scrape_amazon(url):
    """
    Scrapes product details from an Amazon URL.
    Note: Amazon frequently blocks scrapers with CAPTCHAs.
    Uses multiple strategies: JSON-LD > Meta Tags > CSS selectors.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }

    try:
        response = requests.get(url, headers=headers, timeout=6)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        title = None
        price = None
        rating = None
        reviews = None
        image_url = None

        # ── Strategy 1: JSON-LD Schema ────────────────────────────────
        for s in soup.find_all('script', type='application/ld+json'):
            try:
                if not s.string:
                    continue
                data = json.loads(s.string)
                if isinstance(data, list):
                    data = data[0]
                if not isinstance(data, dict):
                    continue
                if data.get('@type') == 'Product':
                    title = title or data.get('name')
                    img = data.get('image')
                    if img and not image_url:
                        image_url = img[0] if isinstance(img, list) else img
                    if not price and 'offers' in data:
                        offers = data['offers']
                        offer = offers[0] if isinstance(offers, list) else offers
                        p = offer.get('price') or offer.get('lowPrice')
                        if p:
                            price = f"₹{int(float(str(p))):,}"
                    if 'aggregateRating' in data:
                        agg = data['aggregateRating']
                        rating = rating or str(agg.get('ratingValue', ''))
                        reviews = reviews or str(agg.get('reviewCount') or agg.get('ratingCount', ''))
            except Exception:
                pass

        # ── Strategy 2: Amazon-specific CSS selectors ─────────────────
        # Title
        if not title:
            el = soup.find('span', id='productTitle')
            if el:
                title = el.get_text(strip=True)

        # Price
        if not price:
            # Try whole + fraction
            whole = soup.find('span', class_='a-price-whole')
            fraction = soup.find('span', class_='a-price-fraction')
            if whole:
                w = whole.get_text(strip=True).rstrip('.')
                f = fraction.get_text(strip=True) if fraction else '00'
                price = f"₹{w}.{f}"
            else:
                for sel in [
                    ('span', 'a-offscreen'),
                    ('span', 'apexPriceToPay'),
                ]:
                    el = soup.find(sel[0], class_=sel[1])
                    if el:
                        text = el.get_text(strip=True)
                        if '₹' in text or re.search(r'\d{3,}', text):
                            price = text
                            break

        # Rating
        if not rating:
            el = soup.find('span', class_='a-icon-alt')
            if el:
                r = el.get_text(strip=True).split(' ')[0]
                if re.match(r'^\d+\.?\d*$', r):
                    rating = r

        # Review count
        if not reviews:
            el = soup.find('span', id='acrCustomerReviewText')
            if el:
                nums = re.findall(r'[\d,]+', el.get_text())
                if nums:
                    reviews = nums[0].replace(',', '')

        # Image
        if not image_url:
            el = soup.find('img', id='landingImage') or soup.find('img', id='imgBlkFront')
            if el:
                image_url = el.get('data-old-hires') or el.get('src') or ''

        # ── Strategy 3: Meta tag fallback ─────────────────────────────
        if not title:
            og = soup.find('meta', property='og:title')
            if og:
                raw = og.get('content', '')
                raw = re.sub(r'\s*[-|].*?(Amazon|Buy).*$', '', raw, flags=re.IGNORECASE)
                title = raw.strip() or None

        if not image_url:
            og = soup.find('meta', property='og:image')
            if og:
                image_url = og.get('content', '') or ''

        # ── Fallback from page title ───────────────────────────────────
        if not title and soup.title and soup.title.string:
            raw = soup.title.string
            raw = re.sub(r'Amazon\.in\s*[:|-]?\s*', '', raw, flags=re.IGNORECASE)
            raw = re.sub(r'\s*(Buy|at Low Price|Online).*$', '', raw, flags=re.IGNORECASE)
            raw = raw.split('|')[0].strip()
            if raw:
                title = raw

        # ── URL-based title (no random data) ──────────────────────────
        if not title:
            url_parts = url.split('/')
            for part in url_parts:
                if '-' in part and len(part) > 10 and '?' not in part:
                    title = part.replace('-', ' ').title()
                    break
            title = title or "Amazon Product"

        return {
            'platform': 'Amazon',
            'name': title,
            'price': price or "Price unavailable",
            'rating': rating or "N/A",
            'reviews': reviews or "N/A",
            'image': image_url or "",
            'status': 'success'
        }

    except Exception as e:
        print(f"Amazon Scraper Error: {e}")
        url_parts = url.split('/')
        fallback_title = "Amazon Product"
        for part in url_parts:
            if '-' in part and len(part) > 10 and '?' not in part:
                fallback_title = part.replace('-', ' ').title()
                break

        return {
            'platform': 'Amazon',
            'name': fallback_title,
            'price': "Price unavailable",
            'rating': "N/A",
            'reviews': "N/A",
            'image': "",
            'status': 'success'
        }
