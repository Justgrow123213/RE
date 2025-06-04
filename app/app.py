from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import json
import logging
from datetime import datetime
from app.scraper import DDPropertyScraper

# Try to import Selenium scraper
try:
    from app.selenium_scraper import SeleniumDDPropertyScraper
    selenium_available = True
    logging.info("Selenium scraper is available")
except Exception as e:
    logging.error(f"Selenium not available: {str(e)}")
    selenium_available = False

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_testing')

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html', selenium_available=selenium_available)

@app.route('/search', methods=['POST'])
def search():
    # Get search parameters from form
    search_params = {
        'listing_type': request.form.get('listing_type', 'sale'),
        'location': request.form.get('location', 'bangkok'),
        'property_type': request.form.get('property_type'),
        'price_min': request.form.get('price_min'),
        'price_max': request.form.get('price_max'),
        'bedrooms': request.form.get('bedrooms'),
        'bathrooms': request.form.get('bathrooms')
    }
    
    # Remove empty parameters
    search_params = {k: v for k, v in search_params.items() if v}
    
    # Check if use_selenium parameter is provided
    use_selenium = request.form.get('use_selenium') == 'true'
    
    # Initialize appropriate scraper
    if use_selenium and selenium_available:
        scraper = SeleniumDDPropertyScraper()
        logging.info("Using Selenium scraper")
    else:
        scraper = DDPropertyScraper()
        logging.info("Using regular scraper")
    
    # Search for properties
    properties = scraper.search_properties(search_params)
    
    # Save search results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/search_results_{timestamp}.json"
    scraper.save_to_json(properties, filename)
    
    # Store the filename in session for later use
    session_data = {
        'filename': filename,
        'properties': properties,
        'search_params': search_params,
        'use_selenium': use_selenium
    }
    
    with open(f"data/session_{timestamp}.json", 'w', encoding='utf-8') as f:
        json.dump(session_data, f, ensure_ascii=False, indent=4)
    
    return redirect(url_for('results', session_id=timestamp, use_selenium='true' if use_selenium else 'false'))

@app.route('/results/<session_id>')
def results(session_id):
    try:
        with open(f"data/session_{session_id}.json", 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        properties = session_data.get('properties', [])
        search_params = session_data.get('search_params', {})
        use_selenium = request.args.get('use_selenium') == 'true'
        
        return render_template('results.html', 
                              properties=properties, 
                              search_params=search_params,
                              session_id=session_id,
                              use_selenium=use_selenium)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/group/<session_id>', methods=['POST'])
def group_properties(session_id):
    try:
        # Get the category to group by
        category = request.form.get('category', 'location')
        
        if not category:
            return jsonify({'error': 'No category specified'}), 400
        
        # Load session data
        with open(f"data/session_{session_id}.json", 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        properties = session_data.get('properties', [])
        use_selenium = session_data.get('use_selenium', False)
        
        # Initialize appropriate scraper
        if use_selenium and selenium_available:
            scraper = SeleniumDDPropertyScraper()
            logging.info("Using Selenium scraper for grouping")
        else:
            scraper = DDPropertyScraper()
            logging.info("Using regular scraper for grouping")
        
        # Map frontend category names to backend category names
        category_mapping = {
            'location': 'location',
            'bedrooms': 'bedrooms',
            'bathrooms': 'bathrooms',
            'price_range': 'price_range',
            'area_range': 'area_range'
        }
        
        # Use the mapped category or default to location
        backend_category = category_mapping.get(category, 'location')
        
        # Group properties by category
        grouped_properties = scraper.group_properties_by_category(properties, backend_category)
        
        # Save grouped results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/grouped_by_{category}_{timestamp}.json"
        scraper.save_to_json(grouped_properties, filename)
        
        return render_template('grouped.html', 
                              grouped_properties=grouped_properties, 
                              category=category,
                              session_id=session_id,
                              use_selenium=use_selenium)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/property/<path:property_url>')
def property_details(property_url):
    try:
        # Check if use_selenium parameter is provided
        use_selenium = request.args.get('use_selenium') == 'true'
        
        # Initialize appropriate scraper
        if use_selenium and selenium_available:
            scraper = SeleniumDDPropertyScraper()
            logging.info("Using Selenium scraper for property details")
        else:
            scraper = DDPropertyScraper()
            logging.info("Using regular scraper for property details")
        
        # Get property details
        property_url = "https://" + property_url if not property_url.startswith('http') else property_url
        details = scraper.get_property_details(property_url)
        
        return render_template('property.html', property=details)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/api/search', methods=['POST'])
def api_search():
    try:
        # Get search parameters from JSON
        search_params = request.json
        
        # Initialize scraper
        scraper = DDPropertyScraper()
        
        # Search for properties
        properties = scraper.search_properties(search_params)
        
        return jsonify(properties)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/group', methods=['POST'])
def api_group():
    try:
        # Get properties and category from JSON
        data = request.json
        properties = data.get('properties', [])
        category = data.get('category', 'location')
        
        if not category:
            return jsonify({'error': 'No category specified'}), 400
        
        # Initialize scraper
        scraper = DDPropertyScraper()
        
        # Map frontend category names to backend category names
        category_mapping = {
            'location': 'location',
            'bedrooms': 'bedrooms',
            'bathrooms': 'bathrooms',
            'price_range': 'price_range',
            'area_range': 'area_range'
        }
        
        # Use the mapped category or default to location
        backend_category = category_mapping.get(category, 'location')
        
        # Group properties by category
        grouped_properties = scraper.group_properties_by_category(properties, backend_category)
        
        return jsonify(grouped_properties)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=12000, debug=True)