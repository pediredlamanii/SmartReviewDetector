import sys
import os

# Add current directory to path so we can import scrapers
sys.path.insert(0, os.path.abspath('.'))

from scrapers.amazon_scraper import scrape_amazon

# Test scraping the exact Amazon URL
url = "https://www.amazon.in/realme-Bluetooth-Wireless-Playback-Charging/dp/B0DFWKK9Z6"
print("Scraping URL:", url)
res = scrape_amazon(url)
print("Result:", res)
