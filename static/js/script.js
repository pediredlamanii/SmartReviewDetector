document.addEventListener('DOMContentLoaded', () => {
    const analyzeBtn = document.getElementById('analyze-btn');
    const productUrlInput = document.getElementById('product-url');
    const loadingDiv = document.getElementById('loading');

    if (analyzeBtn && productUrlInput) {
        analyzeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const url = productUrlInput.value.trim();
            
            if (!url) {
                alert('Please enter a valid product URL.');
                return;
            }

            // Show loading spinner
            loadingDiv.classList.remove('hidden');
            analyzeBtn.disabled = true;

            // Phase 2: Actual fetch API call to Flask backend
            fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    console.log('Backend response:', data);
                    // Store the product data in session storage to use on the next page
                    sessionStorage.setItem('scrapedProduct', JSON.stringify(data));
                    // Redirect to result page after successful backend communication
                    window.location.href = '/result';
                } else {
                    alert('Error analyzing product: ' + (data.message || 'Unknown error'));
                    loadingDiv.classList.add('hidden');
                    analyzeBtn.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Something went wrong connecting to the server.');
                loadingDiv.classList.add('hidden');
                analyzeBtn.disabled = false;
            });
        });
    }

    // Logic for Result Page to load dynamic data
    if (window.location.pathname === '/result') {
        const productDataString = sessionStorage.getItem('scrapedProduct');
        if (productDataString) {
            const data = JSON.parse(productDataString);
            const product = data.product;
            
            if (product && product.status === 'success') {
                document.getElementById('res-title').textContent = product.name || 'Unknown Product';
                document.getElementById('res-price').textContent = product.price || 'N/A';
                
                // Format rating string
                const ratingText = `⭐ ${product.rating || '0.0'} (${product.reviews || '0'} reviews)`;
                document.getElementById('res-rating').textContent = ratingText;
                
                if (product.image) {
                    document.getElementById('res-image').src = product.image;
                }
                
                document.getElementById('res-brand').textContent = `Platform: ${data.platform} | ID: ${data.product_id}`;
                
                // Phase 5: Inject Comparison & Recommendation Data
                const comp = data.comparison;
                if (comp) {
                    document.getElementById('res-trust-score').textContent = comp.trust_score + '%';
                    document.getElementById('res-trust-label').textContent = comp.trust_label;
                    
                    document.getElementById('rec-best-price').textContent = comp.best_price;
                    document.getElementById('rec-highest-trust').textContent = comp.highest_trust;
                    document.getElementById('rec-recommended').textContent = comp.recommended;
                    
                    const tbody = document.getElementById('comparison-tbody');
                    if (tbody) {
                        tbody.innerHTML = '';
                        comp.table.forEach(row => {
                            const tr = document.createElement('tr');
                            if (row.not_found) {
                                tr.innerHTML = `
                                    <td><a href="${row.link}" target="_blank" style="color: #64ffda; text-decoration: none;">${row.platform} ↗</a></td>
                                    <td colspan="5" style="text-align: center; color: #a0aec0; font-style: italic;">Exact product not found on ${row.platform}</td>
                                `;
                            } else {
                                const fakeClass = row.fake_pct > 15 ? 'bad-stat' : 'good-stat';
                                tr.innerHTML = `
                                    <td><a href="${row.link}" target="_blank" style="color: #64ffda; text-decoration: none;">${row.platform} ↗</a></td>
                                    <td>${row.price}</td>
                                    <td>${row.rating}</td>
                                    <td>${row.reviews}</td>
                                    <td><span class="${fakeClass}">${row.fake_pct}%</span></td>
                                    <td>${row.adj_rating}</td>
                                `;
                            }
                            tbody.appendChild(tr);
                        });
                    }
                }
                
            } else if (product && product.status === 'error') {
                document.getElementById('res-title').textContent = "Scraping Failed for this product";
                document.getElementById('res-brand').textContent = product.message || "Anti-scraping protection blocked us.";
            }
        }
    }
});
