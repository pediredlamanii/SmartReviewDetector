import random

def clean_price(price_str):
    """
    Cleans a price string like '₹3,534' or '1,499.' into a float.
    Returns 0.0 if not parseable.
    """
    if not price_str or price_str in ("Unknown Price", "Price unavailable", "N/A", "-"):
        return 0.0

    cleaned = price_str.replace('₹', '').replace(',', '').strip()
    # Remove trailing dot
    if cleaned.endswith('.'):
        cleaned = cleaned[:-1]
    # Remove decimal fraction if present (e.g. 1499.00 → 1499)
    cleaned = cleaned.split('.')[0]

    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def format_price(price_float):
    """
    Formats a float back into a string like '₹3,534'.
    """
    return f"₹{int(price_float):,}"

def generate_comparison_data(scraped_product):
    """
    Takes the actual scraped product data and generates simulated 
    comparison data for other platforms to ensure the presentation works smoothly.
    """
    original_url = scraped_product.get('url', '#')
    random.seed(original_url)
    
    base_price = clean_price(scraped_product.get('price', '0'))
    
    if base_price == 0:
        base_price = random.randint(1000, 5000) # Fallback if price parsing fails
        
    try:
        base_rating = float(scraped_product.get('rating', '4.0'))
    except ValueError:
        base_rating = 4.0
        
    try:
        rev_str = scraped_product.get('reviews', '1000')
        if not rev_str or rev_str in ('N/A', '-', ''):
            rev_str = '1000'
        base_reviews = int(rev_str.replace(',', '').replace('(', '').replace(')', ''))
    except ValueError:
        base_reviews = 1000

    platforms = ['Amazon', 'Flipkart']
    original_platform = scraped_product.get('platform', 'Amazon')
    original_url = scraped_product.get('url', '#')
    
    from urllib.parse import quote
    import requests
    from bs4 import BeautifulSoup

    def get_direct_link(domain, query):
        """Scrapes Bing search and decodes the click-tracking URL to get the exact product link."""
        import base64
        import urllib.parse as urlparse
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        search_url = f"https://www.bing.com/search?q=site:{domain}+{quote(query)}"
        try:
            res = requests.get(search_url, headers=headers, timeout=3)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                links = soup.select('li.b_algo h2 a')
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
                                if domain in decoded_url:
                                    return decoded_url
                            except Exception:
                                pass
        except Exception:
            pass
        return None

    import re
    # Extract the first 3 words of the product name for a highly accurate search query
    raw_name = scraped_product.get('name', 'Product')
    # 1. Remove anything in parentheses (like model numbers which break search)
    clean_str = re.sub(r'\(.*?\)', '', raw_name)
    # 2. Remove all non-alphanumeric characters except spaces
    clean_str = re.sub(r'[^a-zA-Z0-9\s]', '', clean_str)
    # 3. Take first 3 words for a broad, accurate search match
    words = clean_str.split()
    search_words = words[:3] if len(words) >= 3 else words
    search_query_plain = " ".join(search_words)
    search_query_encoded = quote(search_query_plain)
    
    comparison_results = []
    
    for platform in platforms:
        # Determine the link
        row_link = "#"
        if platform == original_platform:
            row_link = original_url
        else:
            # Map platform to its domain
            domain = ""
            if platform == 'Amazon': domain = "amazon.in"
            elif platform == 'Flipkart': domain = "flipkart.com"
            
            if domain:
                found_link = get_direct_link(domain, search_query_plain)
                if found_link:
                    row_link = found_link
                else:
                    row_link = f"/go?platform={platform}&q={search_query_encoded}"
            else:
                row_link = f"/go?platform={platform}&q={search_query_encoded}"

        if platform == original_platform:
            # Use real data, but we still generate fake review stats for Phase 6 preview
            fake_review_pct = random.randint(5, 25)
            adj_rating = max(1.0, round(base_rating - (fake_review_pct / 100.0 * 2.0), 1))
            
            comparison_results.append({
                'platform': platform,
                'price': format_price(base_price),
                'price_val': base_price,
                'rating': str(base_rating),
                'reviews': f"{base_reviews:,}",
                'fake_pct': fake_review_pct,
                'adj_rating': str(adj_rating),
                'link': row_link
            })
        else:
            # Try to scrape the real data from the found link!
            real_data = None
            not_found = False
            
            if not row_link.startswith('/go') and row_link != '#':
                try:
                    if platform == 'Amazon':
                        from scrapers.amazon_scraper import scrape_amazon
                        real_data = scrape_amazon(row_link)
                    elif platform == 'Flipkart':
                        from scrapers.flipkart_scraper import scrape_flipkart
                        real_data = scrape_flipkart(row_link)
                except Exception as e:
                    print(f"Failed to live-scrape {platform}: {e}")
            
            if real_data and 'price' in real_data and real_data['price'] != "Unknown Price":
                try:
                    sim_price = float(str(real_data['price']).replace('₹', '').replace(',', '').strip())
                except:
                    sim_price = base_price
                try:
                    sim_rating = float(real_data['rating'])
                except:
                    sim_rating = base_rating
                try:
                    import re
                    clean_rev = re.sub(r'[^0-9]', '', str(real_data['reviews']))
                    sim_reviews = int(clean_rev) if clean_rev else base_reviews
                except:
                    sim_reviews = base_reviews
            elif row_link.startswith('/go'):
                not_found = True
                sim_price = 0
                sim_rating = 0
                sim_reviews = 0
            else:
                # Fallback to simulated data only if we found a link but scraper was blocked
                price_variation = random.uniform(-0.08, 0.08)
                sim_price = base_price * (1 + price_variation)
                rating_variation = random.uniform(-0.3, 0.3)
                sim_rating = min(5.0, max(1.0, round(base_rating + rating_variation, 1)))
                sim_reviews = max(10, int(base_reviews * random.uniform(0.1, 1.5)))
                
            fake_review_pct = random.randint(2, 35) if not not_found else 0
            adj_rating = max(1.0, round(sim_rating - (fake_review_pct / 100.0 * 2.0), 1)) if not not_found else 0
            
            comparison_results.append({
                'platform': platform,
                'price': format_price(sim_price) if not not_found else '-',
                'price_val': sim_price,
                'rating': str(sim_rating) if not not_found else '-',
                'reviews': f"{sim_reviews:,}" if not not_found else '-',
                'fake_pct': fake_review_pct,
                'adj_rating': str(adj_rating) if not not_found else '-',
                'link': row_link,
                'not_found': not_found
            })

            
    # Calculate Recommendations
    valid_results = [r for r in comparison_results if not r.get('not_found', False)]
    best_price_item = min(valid_results, key=lambda x: x['price_val']) if valid_results else comparison_results[0]
    highest_trust_item = min(valid_results, key=lambda x: x['fake_pct']) if valid_results else comparison_results[0]
    
    
    # Calculate overall Trust Score for the original product
    orig_item = next(item for item in comparison_results if item['platform'] == original_platform)
    trust_score = 100 - orig_item['fake_pct']
    
    # Reset random seed so it doesn't affect other parts of the app
    random.seed()
    
    return {
        'table': comparison_results,
        'best_price': f"{best_price_item['platform']} ({best_price_item['price']})" if not best_price_item.get('not_found') else "N/A",
        'highest_trust': f"{highest_trust_item['platform']} ({100 - highest_trust_item['fake_pct']}%)" if not highest_trust_item.get('not_found') else "N/A",
        'recommended': highest_trust_item['platform'] if not highest_trust_item.get('not_found') else "N/A",
        'trust_score': trust_score,
        'trust_label': 'Highly Trusted' if trust_score > 80 else ('Average Trust' if trust_score > 60 else 'Low Trust')
    }
