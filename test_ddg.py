import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import re

def test_bing():
    domain = "amazon.in"
    raw_query = "realme Buds T110 (RMA2306)"
    
    # 1. Remove anything in parentheses
    clean_str = re.sub(r'\(.*?\)', '', raw_query)
    # 2. Remove all non-alphanumeric characters except spaces
    clean_str = re.sub(r'[^a-zA-Z0-9\s]', '', clean_str)
    # 3. Take first 3 words
    words = clean_str.split()
    query = " ".join(words[:3])
    
    print("Cleaned query:", query)
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    search_url = f"https://www.bing.com/search?q=site:{domain}+{quote(query)}"
    
    print(f"Requesting: {search_url}")
    try:
        res = requests.get(search_url, headers=headers, timeout=10)
        print(f"Status: {res.status_code}")
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        import base64
        import urllib.parse as urlparse

        links = soup.select('li.b_algo h2 a')
        if links:
            for link in links:
                href = link.get('href', '')
                parsed = urlparse.urlparse(href)
                query_params = urlparse.parse_qs(parsed.query)
                if 'u' in query_params:
                    u_val = query_params['u'][0]
                    if u_val.startswith('a1'):
                        b64_str = u_val[2:]
                        b64_str += "=" * ((4 - len(b64_str) % 4) % 4)
                        try:
                            decoded_url = base64.urlsafe_b64decode(b64_str).decode('utf-8')
                            print(f"Decoded: {decoded_url}")
                            if domain in decoded_url:
                                print(f"*** EXACT MATCH FOUND: {decoded_url} ***")
                                break
                        except Exception as e:
                            print("Decode error:", e)
        else:
            print("Did not find Bing links.")
                    
    except Exception as e:
        print("Error:", e)

test_bing()
