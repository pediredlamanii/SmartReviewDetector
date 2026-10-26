import re
from urllib.parse import urlparse, parse_qs

def detect_platform(url):
    """
    Detects the e-commerce platform from the given URL.
    Returns the platform name or 'Unknown'.
    """
    if not url:
        return 'Unknown'
    url_lower = url.lower()
    if 'amazon' in url_lower:
        return 'Amazon'
    elif 'flipkart' in url_lower or 'fkrt.it' in url_lower:
        return 'Flipkart'
    elif 'meesho' in url_lower:
        return 'Meesho'
    elif 'myntra' in url_lower:
        return 'Myntra'
    elif 'reliancedigital' in url_lower:
        return 'Reliance Digital'
    return 'Unknown'

def extract_product_id(url, platform):
    """
    Extracts the unique product ID (like ASIN for Amazon or FSN/Item ID for Flipkart) from the URL.
    """
    if not url:
        return "Unknown_ID"

    if platform == 'Amazon':
        # Amazon ASIN is a 10-character alphanumeric string
        match = re.search(r'/(?:dp|gp/product|ASIN|d)/([A-Z0-9]{10})', url, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        # Fallback to any 10-char ASIN query parameter
        match_q = re.search(r'(?:asin|productId)=([A-Z0-9]{10})', url, re.IGNORECASE)
        if match_q:
            return match_q.group(1).upper()

    elif platform == 'Flipkart':
        # 1. Check query parameter pid=
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if 'pid' in params and params['pid']:
            return params['pid'][0]
        
        # 2. Check regex pid= in URL string
        match_pid = re.search(r'pid=([a-zA-Z0-9]+)', url, re.IGNORECASE)
        if match_pid:
            return match_pid.group(1)

        # 3. Check /p/itm... (Flipkart item ID)
        match_itm = re.search(r'/p/(itm[a-zA-Z0-9]+)', url, re.IGNORECASE)
        if match_itm:
            return match_itm.group(1)

        # 4. Check any /p/ segment
        match_p = re.search(r'/p/([a-zA-Z0-9]+)', url, re.IGNORECASE)
        if match_p:
            return match_p.group(1)

        # 5. Short link ID: e.g. dl.flipkart.com/s/([a-zA-Z0-9_]+)
        match_short = re.search(r'/s/([a-zA-Z0-9_]+)', url)
        if match_short:
            return f"FS_{match_short.group(1)}"

    return "Product_Item"
