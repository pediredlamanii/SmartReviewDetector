import requests
from bs4 import BeautifulSoup

def search_flipkart(query):
    url = f"https://www.flipkart.com/search?q={query}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    try:
        res = requests.get(url, headers=headers)
        with open('test_fk.html', 'w', encoding='utf-8') as f:
            f.write(res.text)
    except Exception as e:
        print(e)
    return None

print(search_flipkart("earthsave Insulated Lunch"))
