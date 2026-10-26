from flask import Flask, render_template, request, jsonify, redirect, session, flash, url_for  # pyrefly: ignore [missing-import]
import sys
import os
import requests  # pyrefly: ignore [missing-import]
from bs4 import BeautifulSoup  # pyrefly: ignore [missing-import]
import urllib.parse
from werkzeug.security import generate_password_hash, check_password_hash  # pyrefly: ignore [missing-import]

# Add current directory to path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.platform_detector import detect_platform, extract_product_id
from utils.comparison_engine import generate_comparison_data
from utils.nlp_engine import analyze_review_text
from scrapers.amazon_scraper import scrape_amazon
from scrapers.flipkart_scraper import scrape_flipkart
from utils.db import init_db, add_user, get_user_by_email

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_auth'

# Initialize database
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/debug_ip')
def debug_ip():
    target = request.args.get('url', 'https://www.flipkart.com/vivo-t4-lite-5g-titanium-gold-2026-4gb-64gb/p/itm49fb53d099f3c?pid=MOBHNCRK44PF7QEN')
    try:
        r = requests.get(target, headers={'User-Agent': 'WhatsApp/2.21.12.21 A', 'Accept': '*/*'}, timeout=4)
        return jsonify({'status': r.status_code, 'len': len(r.text), 'snippet': r.text[:300]})
    except Exception as e:
        return jsonify({'error': str(e), 'type': type(e).__name__})

@app.route('/analyze', methods=['POST'])
def analyze():
    # Phase 2 & 3 & 4: Receive URL, Detect Platform, Scrape
    data = request.get_json()
    url = data.get('url') if data else None
    
    if not url:
        return jsonify({"status": "error", "message": "No URL provided"})

    # Phase 3: Detect Platform
    platform = detect_platform(url)
    product_id = extract_product_id(url, platform)
    
    print(f"\n--- Phase 3 & 4 Backend Check ---")
    print(f"Received URL: {url}")
    print(f"Detected Platform: {platform}")
    print(f"Product ID: {product_id}")
    
    # Phase 4: Scrape Product Data
    product_data = {}
    if platform == 'Amazon':
        product_data = scrape_amazon(url)
    elif platform == 'Flipkart':
        product_data = scrape_flipkart(url)
    else:
        product_data = {
            'platform': platform,
            'status': 'error',
            'message': f'Scraping for {platform} is not supported yet.'
        }
        
    try:
        print(f"Scraped Data: {product_data}")
    except UnicodeEncodeError:
        print("Scraped Data: [Contains Unicode characters that cannot be printed to this console]")
    print(f"---------------------------------\n")
    
    if product_data.get('status') == 'error':
        return jsonify({
            "status": "error",
            "message": product_data.get('message', 'Scraping failed.')
        })
        
    # Inject original URL so frontend can create clickable links
    product_data['url'] = url
        
    # Phase 5: Generate Comparison and Fake Review Data
    comparison_data = generate_comparison_data(product_data)

    # Ensure main product card price is never 'Price unavailable' if comparison resolved a price
    orig_table_item = next((item for item in comparison_data.get('table', []) if item['platform'] == platform), None)
    if orig_table_item and (not product_data.get('price') or product_data.get('price') == "Price unavailable"):
        if orig_table_item.get('price') and orig_table_item['price'] != "Price unavailable":
            product_data['price'] = orig_table_item['price']
    
    return jsonify({
        "status": "success",
        "platform": platform,
        "product_id": product_id,
        "product": product_data,
        "comparison": comparison_data
    })

@app.route('/result')
def result():
    return render_template('result.html')

@app.route('/detect')
def detect():
    return render_template('detect.html')

@app.route('/go')
def smart_redirect():
    """
    Backend redirect engine: Redirects to the most reliable search page 
    for the product since direct URL scraping is blocked by Captchas.
    """
    platform = request.args.get('platform', '')
    query = request.args.get('q', '')
    
    # Seamless Fallback to search pages
    if platform == 'Amazon':
        return redirect(f"https://www.amazon.in/s?k={query}")
    elif platform == 'Flipkart':
        return redirect(f"https://www.flipkart.com/search?q={query}")
    else:
        return redirect("/")

@app.route('/analyze_review', methods=['POST'])
def analyze_review():
    data = request.get_json()
    text = data.get('text')
    return jsonify(analyze_review_text(text))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = get_user_by_email(email)
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
            
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
        else:
            hashed_password = generate_password_hash(password)
            if add_user(email, hashed_password):
                flash('Account created successfully! Please login.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Email is already registered.', 'error')
                
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
