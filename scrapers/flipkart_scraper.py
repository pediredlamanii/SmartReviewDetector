import requests  # pyrefly: ignore [missing-import]
from bs4 import BeautifulSoup  # pyrefly: ignore [missing-import]
import json
import re

def scrape_flipkart(url):
    """
    Scrapes product details from a Flipkart URL using multiple robust fallback strategies.
    Priority: JSON-LD Schema > Meta Tags > CSS Selectors > HTML Regex > URL-based fallback
    """
    # NOTE: Do NOT include 'Accept-Encoding': 'br' because requests does not decompress
    # brotli without external libraries, which causes binary content and empty HTML parsing.
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
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

        # ── Strategy 1: JSON-LD Schema (Highest Fidelity) ────────────────
        scripts = soup.find_all('script', type='application/ld+json')
        for s in scripts:
            content = s.string or s.text or (s.get_text() if hasattr(s, 'get_text') else '')
            if not content or not content.strip():
                continue
            try:
                data = json.loads(content)
                # Could be a single dict, list of dicts, or graph
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
                        # Product Title
                        if not title and item.get('name'):
                            title = str(item['name']).strip()

                        # Product Image
                        if not image_url and item.get('image'):
                            img = item['image']
                            if isinstance(img, list) and img:
                                image_url = str(img[0]).strip()
                            elif isinstance(img, str):
                                image_url = img.strip()

                        # Product Price
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

                        # Aggregate Rating & Reviews
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

        # ── Strategy 2: Open Graph / Twitter Meta Tags ───────────────────
        if not title:
            og_title = soup.find('meta', property='og:title') or soup.find('meta', attrs={'name': 'twitter:title'})
            if og_title and og_title.get('content'):
                raw = og_title['content']
                raw = re.sub(r'^Buy\s+', '', raw, flags=re.IGNORECASE)
                raw = re.sub(r'\s+(Online|at Best Price|Price in India).*$', '', raw, flags=re.IGNORECASE)
                raw = raw.split('|')[0].strip()
                if raw:
                    title = raw

        if not image_url:
            og_img = (
                soup.find('meta', property='og:image') or
                soup.find('meta', attrs={'name': 'twitter:image'}) or
                soup.find('link', rel='image_src')
            )
            if og_img:
                image_url = og_img.get('content') or og_img.get('href') or None

        # ── Strategy 3: CSS Selectors ───────────────────────────────────
        # Title
        if not title:
            for sel in [
                ('span', 'B_NuCI'),
                ('span', 'VU-Tz5'),
                ('h1', 'yhB1nd'),
                ('span', '_35KyD6'),
                ('div', '_4rR01T'),
                ('span', 'x+_JAnf'),
            ]:
                el = soup.find(sel[0], class_=sel[1])
                if el:
                    t_text = el.get_text(strip=True)
                    if len(t_text) > 3:
                        title = t_text
                        break

        # Page <title> fallback
        if not title and soup.title and soup.title.string:
            raw = soup.title.string
            raw = re.sub(r'^Buy\s+', '', raw, flags=re.IGNORECASE)
            raw = re.sub(r'\s+(Online|at Best Price|Price in India).*$', '', raw, flags=re.IGNORECASE)
            raw = raw.split('|')[0].strip()
            if len(raw) > 3:
                title = raw

        # Price Selectors
        if not price:
            for sel in [
                ('div', 'Nx9bqj CxhGGd'),
                ('div', '_30jeq3 _16Jk6d'),
                ('div', 'Nx9bqj'),
                ('div', '_30jeq3'),
                ('div', 'CEmiEU'),
                ('div', 'UOCQB1'),
                ('div', '_16Jk6d'),
                ('div', '_3qQ9m1'),
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

        # Rating Selectors
        if not rating:
            for sel in [
                ('div', 'XQDdHH'),
                ('div', '_3LWZlK'),
                ('div', 'gUuXy-'),
                ('div', 'ipqd2A'),
            ]:
                el = soup.find(sel[0], class_=sel[1])
                if el:
                    r_text = el.get_text(strip=True)
                    if re.match(r'^\d+(\.\d+)?$', r_text):
                        rating = r_text
                        break

        # Reviews Selectors
        if not reviews:
            for sel in [
                ('span', 'Wphh3N'),
                ('span', '_2_R_DZ'),
                ('span', 'Y1HWO0'),
                ('span', '_13vcmD'),
            ]:
                el = soup.find(sel[0], class_=sel[1])
                if el:
                    r_text = el.get_text(strip=True)
                    nums = re.findall(r'[\d,]+', r_text)
                    if nums:
                        reviews = nums[0]
                        break

        # Image Selectors
        if not image_url:
            for sel in [
                ('img', 'DByuf4 IZexXJ jLEJ7H'),
                ('img', 'DByuf4'),
                ('img', '_396cs4 _2amPTt _3qGmMb'),
                ('img', '_396cs4'),
                ('img', 'q6DClP'),
                ('img', '_2r_T1I'),
            ]:
                el = soup.find(sel[0], class_=sel[1])
                if el and el.get('src') and 'http' in el.get('src'):
                    image_url = el['src']
                    break

        # ── Strategy 4: Raw HTML Regex Search ───────────────────────────
        if not price:
            p_matches = re.findall(r'₹\s*([0-9,]{3,})', html_text)
            if p_matches:
                clean_num = p_matches[0].replace(',', '')
                if clean_num.isdigit() and int(clean_num) > 100:
                    price = f"₹{int(clean_num):,}"

        if not rating:
            r_match = re.search(r'class="[^"]*(?:XQDdHH|_3LWZlK)[^"]*"[^>]*>([1-5]\.[0-9])', html_text)
            if r_match:
                rating = r_match.group(1)

        if not reviews:
            rev_match = re.search(r'([0-9,]+)\s*(?:Ratings|Reviews)', html_text)
            if rev_match:
                reviews = rev_match.group(1)

        if not image_url:
            img_match = re.search(r'https://rukmini\d*\.flixcart\.com/image/[^\s"\']+\.(?:jpeg|jpg|png|webp)', html_text)
            if img_match:
                image_url = img_match.group(0)

    except Exception as e:
        print(f"Flipkart Scraper HTTP/Parse Error: {e}")

    # ── Final Fallback: URL Slug Parser ─────────────────────────────────
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
        title = title or "Flipkart Product"

    # Default values
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
