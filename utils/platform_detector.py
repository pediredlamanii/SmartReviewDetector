import re

def detect_platform(url):
    """
    Detects the e-commerce platform from the given URL.
    Returns the platform name or 'Unknown'.
    """
    url_lower = url.lower()
    if 'amazon' in url_lower:
        return 'Amazon'
    elif 'flipkart' in url_lower:
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
    Extracts the unique product ID (like ASIN for Amazon) from the URL.
    """
    if platform == 'Amazon':
        # Amazon ASIN is usually a 10-character alphanumeric string after /dp/, /gp/product/, or /ASIN/
        match = re.search(r'/(?:dp|gp/product|ASIN)/([A-Z0-9]{10})', url)
        if match:
            return match.group(1)
            
    elif platform == 'Flipkart':
        # Flipkart product ID (FSN) usually starts with 'p' and is in the 'pid=' query parameter
        match = re.search(r'pid=([A-Z0-9]{16})', url)
        if match:
            return match.group(1)
            
    # For now, return a generic ID or None for other platforms
    return "Unknown_ID"
