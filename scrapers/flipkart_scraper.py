import requests  # pyrefly: ignore [missing-import]
from bs4 import BeautifulSoup  # pyrefly: ignore [missing-import]
import json
import re

def scrape_flipkart(url):
    """
    Scrapes product details from a Flipkart URL using multiple fallback strategies.
    Priority: JSON-LD > Meta Tags > CSS Selectors > URL-based fallback
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
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

        # ── Strategy 1: JSON-LD Schema (Most Reliable) ──────────────────
        scripts = soup.find_all('script', type='application/ld+json')
        for s in scripts:
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
                    # Image
                    img = data.get('image')
                    if img and not image_url:
                        image_url = img[0] if isinstance(img, list) else img
                    # Price
                    if not price and 'offers' in data:
                        offers = data['offers']
                        offer = offers[0] if isinstance(offers, list) else offers
                        p = offer.get('price') or offer.get('lowPrice')
                        if p:
                            price = f"₹{int(float(str(p))):,}"
                    # Rating & Reviews
                    if 'aggregateRating' in data:
                        agg = data['aggregateRating']
                        rating = rating or str(agg.get('ratingValue', ''))
                        reviews = reviews or str(agg.get('reviewCount') or agg.get('ratingCount', ''))
            except Exception:
                pass

        # ── Strategy 2: Open Graph / Meta Tags ──────────────────────────
        if not title:
            og_title = soup.find('meta', property='og:title') or soup.find('meta', attrs={'name': 'twitter:title'})
            if og_title:
                raw = og_title.get('content', '')
                # Remove "Buy <title>" prefix and " Online at Best Price in India" suffix
                raw = re.sub(r'^Buy\s+', '', raw, flags=re.IGNORECASE)
                raw = re.sub(r'\s+(Online|at Best Price).*$', '', raw, flags=re.IGNORECASE)
                title = raw.strip() or None

        if not image_url:
            og_img = soup.find('meta', property='og:image')
            if og_img:
                image_url = og_img.get('content', '') or None

        # ── Strategy 3: CSS Selectors (Multiple generations of Flipkart UI) ─
        # Title — try many known class names
        if not title:
            for sel in [
                {'tag': 'span', 'class': 'B_NuCI'},
                {'tag': 'span', 'class': 'VU-Tz5'},
                {'tag': 'span', 'class': 'x+_JAnf'},
                {'tag': 'h1', 'class': 'yhB1nd'},
                {'tag': 'span', 'class': '_35KyD6'},
                {'tag': 'div', 'class': '_4rR01T'},
            ]:
                el = soup.find(sel['tag'], class_=sel['class'])
                if el:
                    title = el.get_text(strip=True)
                    break

        # Fallback title from page <title>
        if not title and soup.title and soup.title.string:
            raw = soup.title.string
            raw = re.sub(r'^Buy\s+', '', raw, flags=re.IGNORECASE)
            raw = re.sub(r'\s+(Online|at Best Price|Price in India).*$', '', raw, flags=re.IGNORECASE)
            raw = raw.split('|')[0].strip()
            if raw:
                title = raw

        # Price — try many known class names
        if not price:
            for sel in [
                {'tag': 'div', 'class': 'Nx9bqj CxhGGd'},
                {'tag': 'div', 'class': '_30jeq3 _16Jk6d'},
                {'tag': 'div', 'class': '_30jeq3'},
                {'tag': 'div', 'class': 'CEmiEU'},
                {'tag': 'div', 'class': 'UOCQB1'},
                {'tag': 'div', 'class': '_16Jk6d'},
                {'tag': 'div', 'class': '_3qQ9m1'},
            ]:
                el = soup.find(sel['tag'], class_=sel['class'])
                if el:
                    text = el.get_text(strip=True)
                    # Must contain ₹ or digits
                    if '₹' in text or re.search(r'\d{3,}', text):
                        price = text
                        break

        # Rating — try many known class names
        if not rating:
            for sel in [
                {'tag': 'div', 'class': 'XQDdHH'},
                {'tag': 'div', 'class': '_3LWZlK'},
                {'tag': 'div', 'class': 'gUuXy-'},
                {'tag': 'div', 'class': 'ipqd2A'},
            ]:
                el = soup.find(sel['tag'], class_=sel['class'])
                if el:
                    r = el.get_text(strip=True)
                    if re.match(r'^\d+\.?\d*$', r):
                        rating = r
                        break

        # Reviews — try many known class names
        if not reviews:
            for sel in [
                {'tag': 'span', 'class': 'Wphh3N'},
                {'tag': 'span', 'class': '_2_R_DZ'},
                {'tag': 'span', 'class': 'Y1HWO0'},
                {'tag': 'span', 'class': '_13vcmD'},
            ]:
                el = soup.find(sel['tag'], class_=sel['class'])
                if el:
                    text = el.get_text(strip=True)
                    nums = re.findall(r'[\d,]+', text)
                    if nums:
                        reviews = nums[0].replace(',', '')
                        break

        # Image — try many known class names
        if not image_url:
            for sel in [
                {'tag': 'img', 'class': 'DByuf4 IZexXJ jLEJ7H'},
                {'tag': 'img', 'class': '_396cs4 _2amPTt _3qGmMb'},
                {'tag': 'img', 'class': 'q6DClP'},
                {'tag': 'img', 'class': '_2r_T1I'},
            ]:
                el = soup.find(sel['tag'], class_=sel['class'])
                if el and el.get('src'):
                    image_url = el['src']
                    break

        # ── Final Fallback: URL-based smart title (no random prices) ────
        if not title:
            url_parts = url.split('/')
            for part in url_parts:
                if '-' in part and len(part) > 10 and '?' not in part:
                    title = part.replace('-', ' ').title()
                    break
            title = title or "Flipkart Product"

        # Clean up defaults
        price = price or "Price unavailable"
        rating = rating or "N/A"
        reviews = reviews or "N/A"
        image_url = image_url or ""

        return {
            'platform': 'Flipkart',
            'name': title,
            'price': price,
            'rating': rating,
            'reviews': reviews,
            'image': image_url,
            'status': 'success'
        }

    except Exception as e:
        print(f"Flipkart Scraper Error: {e}")
        # URL-based fallback title (no random dummy data)
        url_parts = url.split('/')
        fallback_title = "Flipkart Product"
        for part in url_parts:
            if '-' in part and len(part) > 10 and '?' not in part:
                fallback_title = part.replace('-', ' ').title()
                break

        return {
            'platform': 'Flipkart',
            'name': fallback_title,
            'price': "Price unavailable",
            'rating': "N/A",
            'reviews': "N/A",
            'image': "",
            'status': 'success'
        }
