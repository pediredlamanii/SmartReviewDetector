import requests
import re

url = 'https://www.flipkart.com/oppo-enco-buds3-pro-12-4mm-driver-54hrs-playback-deep-bass-dual-device-pairing-ip55-bluetooth/p/itm38793a1d1f9bb?pid=ACCHETEHKXYPUSK2'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

try:
    res = requests.get(url, headers=headers)
    print('Status:', res.status_code)
    
    with open('flip_test.html', 'w', encoding='utf-8') as f:
        f.write(res.text)
        
    import re
    # Find all elements containing the Rupee symbol and a number, e.g. ₹2,854 or ₹3,005
    prices = re.findall(r'class="([^"]*)"[^>]*>₹([0-9,]+)', res.text)
    print("Prices found:", sorted(list(set(prices))))
    
    # Review counts
    reviews = re.findall(r'class="([^"]*)"[^>]*>([0-9,]+)\s*Ratings', res.text)
    print("Reviews found:", set(reviews))
    
except Exception as e:
    print(e)
