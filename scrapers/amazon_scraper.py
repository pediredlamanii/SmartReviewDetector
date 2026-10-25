import requests  # pyrefly: ignore [missing-import]
from bs4 import BeautifulSoup  # pyrefly: ignore [missing-import]
import re
import json

def scrape_amazon(url):
    """
    Scrapes product details from an Amazon URL.
    Uses multiple robust strategies: JSON-LD Schema > Meta Tags > CSS Selectors > HTML Regex > URL-based fallback
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    title = None
    price = None
    rating = None
    reviews = None
    image_url = None

    try:
        response = requests.get(url, headers=headers, timeout=6)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        html_text = response.text

        # ── Strategy 1: JSON-LD Schema ────────────────────────────────
        scripts = soup.find_all('script', type='application/ld+json')
        for s in scripts:
            content = s.string or s.text or (s.get_text() if hasattr(s, 'get_text') else '')
            if not content or not content.strip():
                continue
            try:
                data = json.loads(content)
                items = []
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    if '@graph' in data and isinstance(data['@graph'], list):
                        items = data['@graph']
                    else:
                        items = [data]

                for item in items:
                    if not isinstance(item, dict):
                        continue
                    item_type = str(item.get('@type', '')).lower()
                    if 'product' in item_type or 'offers' in item:
                        if not title and item.get('name'):
                            title = str(item['name']).strip()
                        if not image_url and item.get('image'):
                            img = item['image']
                            if isinstance(img, list) and img:
                                image_url = str(img[0]).strip()
                            elif isinstance(img, str):
                                image_url = img.strip()
                        if not price and 'offers' in item:
                            offers = item['offers']
                            offer = offers[0] if isinstance(offers, list) and offers else offers
                            if isinstance(offer, dict):
                                p = offer.get('price') or offer.get('lowPrice') or offer.get('highPrice')
                                if p:
                                    try:
                                        p_clean = re.sub(r'[^\d.]', '', str(p))
                                        if p_clean:
                                            price = f"₹{int(float(p_clean)):,}"
                                    except Exception:
                                        pass
                        if 'aggregateRating' in item:
                            agg = item['aggregateRating']
                            if isinstance(agg, dict):
                                if not rating and agg.get('ratingValue'):
                                    rating = str(agg['ratingValue']).strip()
                                if not reviews:
                                    rev_val = agg.get('reviewCount') or agg.get('ratingCount')
                                    if rev_val:
                                        try:
                                            reviews = f"{int(str(rev_val).replace(',', '')):,}"
                                        except Exception:
                                            reviews = str(rev_val).strip()
            except Exception:
                pass

        # ── Strategy 2: Amazon-specific CSS Selectors ─────────────────
        # Title
        if not title:
            el = soup.find('span', id='productTitle')
            if el:
                t_text = el.get_text(strip=True)
                if len(t_text) > 3:
                    title = t_text

        # Price
        if not price:
            # Whole + Fraction
            whole = soup.find('span', class_='a-price-whole')
            fraction = soup.find('span', class_='a-price-fraction')
            if whole:
                w = whole.get_text(strip=True).rstrip('.')
                f = fraction.get_text(strip=True) if fraction else '00'
                try:
                    price = f"₹{int(w.replace(',', '')):,}"
                except Exception:
                    price = f"₹{w}"
            else:
                for sel in [
                    ('span', 'a-offscreen'),
                    ('span', 'apexPriceToPay'),
                    ('span', 'a-price'),
                ]:
                    el = soup.find(sel[0], class_=sel[1])
                    if el:
                        text = el.get_text(strip=True)
                        if '₹' in text or re.search(r'\d{3,}', text):
                            nums = re.findall(r'[\d,]+', text)
                            if nums:
                                val = nums[0].replace(',', '')
                                if val.isdigit() and int(val) > 0:
                                    price = f"₹{int(val):,}"
                                    break

        # Rating
        if not rating:
            el = soup.find('span', class_='a-icon-alt')
            if el:
                r_text = el.get_text(strip=True).split(' ')[0]
                if re.match(r'^\d+(\.\d+)?$', r_text):
                    rating = r_text

        # Review count
        if not reviews:
            el = soup.find('span', id='acrCustomerReviewText')
            if el:
                nums = re.findall(r'[\d,]+', el.get_text())
                if nums:
                    reviews = nums[0]

        # Image
        if not image_url:
            el = soup.find('img', id='landingImage') or soup.find('img', id='imgBlkFront')
            if el:
                image_url = el.get('data-old-hires') or el.get('src') or ''

        # ── Strategy 3: Meta Tag Fallbacks ────────────────────────────
        if not title:
            og = soup.find('meta', property='og:title')
            if og and og.get('content'):
                raw = og['content']
                raw = re.sub(r'\s*[-|].*?(Amazon|Buy).*$', '', raw, flags=re.IGNORECASE)
                raw = raw.strip()
                if len(raw) > 3:
                    title = raw

        if not image_url:
            og = soup.find('meta', property='og:image')
            if og and og.get('content'):
                image_url = og['content']

        # ── Fallback from page <title> ─────────────────────────────────
        if not title and soup.title and soup.title.string:
            raw = soup.title.string
            raw = re.sub(r'Amazon\.in\s*[:|-]?\s*', '', raw, flags=re.IGNORECASE)
            raw = re.sub(r'\s*(Buy|at Low Price|Online).*$', '', raw, flags=re.IGNORECASE)
            raw = raw.split('|')[0].strip()
            if len(raw) > 3:
                title = raw

    except Exception as e:
        print(f"Amazon Scraper Error: {e}")

    # ── Final Fallback: URL Slug Parser ────────────────────────────────
    if not title:
        try:
            url_parts = url.split('/')
            for part in url_parts:
                clean_part = part.split('?')[0]
                if '-' in clean_part and len(clean_part) > 10:
                    title = clean_part.replace('-', ' ').title()
                    break
        except Exception:
            pass
        title = title or "Amazon Product"

    # Clean up defaults
    price = price or "Price unavailable"
    rating = rating or "N/A"
    reviews = reviews or "N/A"
    image_url = image_url or ""

    return {
        'platform': 'Amazon',
        'name': title,
        'price': price,
        'rating': rating,
        'reviews': reviews,
        'image': image_url,
        'status': 'success'
    }
