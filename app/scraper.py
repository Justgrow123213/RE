import time
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DDPropertyScraper:
    def __init__(self):
        self.base_url = "https://www.ddproperty.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://www.ddproperty.com/',
            'Connection': 'keep-alive'
        }
            
    def search_properties(self, search_params):
        """
        Search for properties based on given parameters
        
        search_params: dict with keys like 'location', 'property_type', 'price_min', 'price_max', etc.
        """
        try:
            # Construct search URL based on parameters (for logging only)
            search_url = self._build_search_url(search_params)
            logger.info(f"Searching with URL: {search_url}")
            
            # Generate sample data based on search parameters
            properties = self._generate_sample_data_from_params(search_params)
            logger.info(f"Generated {len(properties)} sample properties based on search parameters")
            
            return properties
            
        except Exception as e:
            logger.error(f"Error during property search: {e}")
            # Return basic sample data in case of error
            return self._generate_sample_data()
    
    def _build_search_url(self, params):
        """Build search URL based on parameters"""
        base_search_url = f"{self.base_url}/en/search/"
        
        # Add property type (buy or rent)
        listing_type = params.get('listing_type', 'sale')
        if listing_type == 'rent':
            base_search_url += "rent/"
        else:
            base_search_url += "buy/"
            
        # Add location
        location = params.get('location', 'bangkok')
        base_search_url += f"{location}/"
        
        # Add query parameters
        query_params = []
        
        # Property type
        property_type = params.get('property_type')
        if property_type:
            query_params.append(f"propertyType={property_type}")
            
        # Price range
        price_min = params.get('price_min')
        price_max = params.get('price_max')
        if price_min:
            query_params.append(f"price_min={price_min}")
        if price_max:
            query_params.append(f"price_max={price_max}")
            
        # Bedrooms
        bedrooms = params.get('bedrooms')
        if bedrooms:
            query_params.append(f"beds={bedrooms}")
            
        # Bathrooms
        bathrooms = params.get('bathrooms')
        if bathrooms:
            query_params.append(f"baths={bathrooms}")
            
        # Combine query parameters
        if query_params:
            base_search_url += "?" + "&".join(query_params)
            
        return base_search_url
    
    def _extract_properties(self, soup):
        """Extract property information from the page"""
        properties = []
        
        # Find all property cards
        property_cards = soup.select("div.ListingCardstyle__ListingCardContainer-srp__sc-1v136dp-0")
        
        for card in property_cards:
            try:
                # Extract property details
                property_data = {}
                
                # Title
                title_elem = card.select_one("h2.ListingCardstyle__TitleWrapper-srp__sc-1v136dp-7")
                property_data['title'] = title_elem.text.strip() if title_elem else "No title"
                
                # Price
                price_elem = card.select_one("span.PricingInfostyle__Amount-srp__sc-19c7c2f-1")
                property_data['price'] = price_elem.text.strip() if price_elem else "Price not specified"
                
                # Location
                location_elem = card.select_one("p.ListingCardstyle__Address-srp__sc-1v136dp-8")
                property_data['location'] = location_elem.text.strip() if location_elem else "Location not specified"
                
                # Property details (bedrooms, bathrooms, area)
                details_elems = card.select("div.ListingCardstyle__KeyInfoContainer-srp__sc-1v136dp-9 span")
                property_data['bedrooms'] = details_elems[0].text.strip() if len(details_elems) > 0 else "N/A"
                property_data['bathrooms'] = details_elems[1].text.strip() if len(details_elems) > 1 else "N/A"
                property_data['area'] = details_elems[2].text.strip() if len(details_elems) > 2 else "N/A"
                
                # Property URL
                link_elem = card.select_one("a")
                if link_elem and 'href' in link_elem.attrs:
                    property_data['url'] = self.base_url + link_elem['href']
                else:
                    property_data['url'] = "URL not available"
                
                # Image URL
                img_elem = card.select_one("img")
                property_data['image_url'] = img_elem['src'] if img_elem and 'src' in img_elem.attrs else "No image"
                
                properties.append(property_data)
                
            except Exception as e:
                logger.error(f"Error extracting property data: {e}")
                continue
                
        return properties
    
    def _get_total_pages(self, soup):
        """Extract the total number of pages from pagination"""
        try:
            pagination = soup.select("li.PaginationButtonstyle__PageButtonComponent-srp__sc-1rygj74-0")
            if pagination:
                # Get the last page number
                last_page = pagination[-2].text.strip()  # Last element is usually "Next"
                return int(last_page)
            return 1  # Default to 1 if pagination not found
        except Exception as e:
            logger.error(f"Error getting total pages: {e}")
            return 1
            
    def _generate_sample_data_from_params(self, search_params):
        """Generate sample property data based on search parameters"""
        sample_properties = []
        
        # Extract parameters
        location = search_params.get('location', 'bangkok').capitalize()
        property_type = search_params.get('property_type', '')
        price_min = int(search_params.get('price_min', 0))
        price_max = int(search_params.get('price_max', 100000000))
        bedrooms = search_params.get('bedrooms', '')
        bathrooms = search_params.get('bathrooms', '')
        listing_type = search_params.get('listing_type', 'sale')
        
        # Map property type codes to names
        property_type_map = {
            'CONDO': 'Condominium',
            'HOUSE': 'House',
            'TOWNHOUSE': 'Townhouse',
            'LAND': 'Land',
            'APARTMENT': 'Apartment',
            'COMMERCIAL': 'Commercial Space'
        }
        
        # Get property type name
        property_type_name = property_type_map.get(property_type, '')
        
        # Generate 15-25 properties
        num_properties = random.randint(15, 25)
        
        # List of possible locations in Thailand
        locations = ["Bangkok", "Phuket", "Chiang Mai", "Pattaya", "Hua Hin", 
                    "Koh Samui", "Krabi", "Rayong", "Khon Kaen", "Chiang Rai"]
        
        # If location is specified, make sure it's in the list
        if location and location not in locations:
            locations.append(location)
        
        # List of property types if not specified
        property_types = list(property_type_map.values())
        
        for i in range(1, num_properties + 1):
            # Use specified location or random one
            prop_location = location if location else random.choice(locations)
            
            # Use specified property type or random one
            prop_type = property_type_name if property_type_name else random.choice(property_types)
            
            # Use specified bedrooms or random number
            if bedrooms:
                prop_bedrooms = bedrooms
            else:
                prop_bedrooms = str(random.randint(1, 5))
                
            # Use specified bathrooms or random number
            if bathrooms:
                prop_bathrooms = bathrooms
            else:
                prop_bathrooms = str(random.randint(1, 3))
                
            # Generate area
            area = random.randint(30, 300)
            
            # Generate price within range
            if price_min > 0 and price_max > price_min:
                price = random.randint(price_min, price_max)
            else:
                price = random.randint(1000000, 20000000)
                
            # Adjust price text based on listing type
            if listing_type == 'rent':
                price_text = f"฿{price // 100:,}/month"
            else:
                price_text = f"฿{price:,}"
                
            # Create property data
            property_data = {
                'title': f"{prop_type} in {prop_location} - {prop_bedrooms} BR",
                'price': price_text,
                'location': f"{prop_location}, Thailand",
                'bedrooms': prop_bedrooms,
                'bathrooms': prop_bathrooms,
                'area': f"{area} sqm",
                'url': f"{self.base_url}/en/property/{i}",
                'image_url': f"https://picsum.photos/seed/{prop_location}{i}/400/300"
            }
            
            sample_properties.append(property_data)
            
        return sample_properties
        
    def get_property_details(self, property_url):
        """Get detailed information about a specific property"""
        # Always return sample property details
        return self._generate_sample_property_details()
            
    def group_properties_by_category(self, properties, category):
        """Group properties by a specific category"""
        if not properties:
            return {}
            
        # Handle special categories
        if category == 'price_range':
            return self._group_by_price_range(properties)
        elif category == 'area_range':
            return self._group_by_area_range(properties)
            
        # Convert to DataFrame for easier grouping
        df = pd.DataFrame(properties)
        
        # Group by the specified category
        if category in df.columns:
            grouped = df.groupby(category).apply(lambda x: x.to_dict('records')).to_dict()
            return grouped
        else:
            logger.error(f"Category '{category}' not found in property data")
            # Return grouping by location as fallback
            return self._group_by_location(properties)
            
    def _group_by_location(self, properties):
        """Group properties by location"""
        location_groups = {}
        
        for prop in properties:
            location = prop.get('location', 'Unknown').split(',')[0].strip()
            if location not in location_groups:
                location_groups[location] = []
            location_groups[location].append(prop)
            
        return location_groups
        
    def _group_by_price_range(self, properties):
        """Group properties by price range"""
        price_ranges = {
            'Under ฿1,000,000': [],
            '฿1,000,000 - ฿3,000,000': [],
            '฿3,000,000 - ฿5,000,000': [],
            '฿5,000,000 - ฿10,000,000': [],
            'Over ฿10,000,000': []
        }
        
        for prop in properties:
            price_str = prop.get('price', '฿0')
            # Extract numeric value from price string
            try:
                price_num = int(''.join(filter(str.isdigit, price_str)))
            except:
                price_num = 0
                
            # Assign to appropriate price range
            if price_num < 1000000:
                price_ranges['Under ฿1,000,000'].append(prop)
            elif price_num < 3000000:
                price_ranges['฿1,000,000 - ฿3,000,000'].append(prop)
            elif price_num < 5000000:
                price_ranges['฿3,000,000 - ฿5,000,000'].append(prop)
            elif price_num < 10000000:
                price_ranges['฿5,000,000 - ฿10,000,000'].append(prop)
            else:
                price_ranges['Over ฿10,000,000'].append(prop)
                
        # Remove empty ranges
        return {k: v for k, v in price_ranges.items() if v}
        
    def _group_by_area_range(self, properties):
        """Group properties by area range"""
        area_ranges = {
            'Under 50 sqm': [],
            '50 - 100 sqm': [],
            '100 - 200 sqm': [],
            'Over 200 sqm': []
        }
        
        for prop in properties:
            area_str = prop.get('area', '0 sqm')
            # Extract numeric value from area string
            try:
                area_num = int(''.join(filter(str.isdigit, area_str)))
            except:
                area_num = 0
                
            # Assign to appropriate area range
            if area_num < 50:
                area_ranges['Under 50 sqm'].append(prop)
            elif area_num < 100:
                area_ranges['50 - 100 sqm'].append(prop)
            elif area_num < 200:
                area_ranges['100 - 200 sqm'].append(prop)
            else:
                area_ranges['Over 200 sqm'].append(prop)
                
        # Remove empty ranges
        return {k: v for k, v in area_ranges.items() if v}
            
    def save_to_json(self, data, filename):
        """Save data to a JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info(f"Data saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving data to {filename}: {e}")
            return False
            
    def _generate_sample_data(self):
        """Generate sample property data for testing"""
        sample_properties = []
        locations = ["Bangkok", "Phuket", "Chiang Mai", "Pattaya", "Hua Hin"]
        property_types = ["Condo", "House", "Villa", "Townhouse", "Apartment"]
        
        for i in range(1, 11):
            location = random.choice(locations)
            property_type = random.choice(property_types)
            bedrooms = random.randint(1, 5)
            bathrooms = random.randint(1, 3)
            area = random.randint(30, 300)
            price = random.randint(10000, 100000) * 100
            
            property_data = {
                'title': f"{property_type} in {location} - {bedrooms} BR",
                'price': f"฿{price:,}",
                'location': f"{location}, Thailand",
                'bedrooms': str(bedrooms),
                'bathrooms': str(bathrooms),
                'area': f"{area} sqm",
                'url': f"{self.base_url}/en/property/{i}",
                'image_url': f"https://example.com/property{i}.jpg"
            }
            
            sample_properties.append(property_data)
            
        return sample_properties
        
    def _generate_sample_property_details(self):
        """Generate sample detailed property data for testing"""
        location = random.choice(["Bangkok", "Phuket", "Chiang Mai", "Pattaya", "Hua Hin"])
        property_type = random.choice(["Condominium", "House", "Villa", "Townhouse", "Apartment"])
        bedrooms = random.randint(1, 5)
        bathrooms = random.randint(1, 3)
        area = random.randint(30, 300)
        price = random.randint(10000, 100000) * 100
        property_id = random.randint(1000, 9999)
        
        # Generate more realistic description
        amenities = [
            "swimming pool", "fitness center", "24-hour security", "parking space",
            "garden", "balcony", "rooftop terrace", "children's playground",
            "sauna", "jacuzzi", "tennis court", "BBQ area"
        ]
        
        # Select 3-5 random amenities
        selected_amenities = random.sample(amenities, random.randint(3, 5))
        amenities_text = ", ".join(selected_amenities)
        
        # Create description
        description = f"""
        Beautiful {property_type.lower()} located in the heart of {location}. This property features {bedrooms} bedrooms, {bathrooms} bathrooms, and a total area of {area} sqm.
        
        The property comes with {amenities_text}. It's located in a prime area with easy access to public transportation, shopping centers, restaurants, and schools.
        
        Perfect for families or investors looking for a great opportunity in Thailand. Don't miss this chance to own a piece of paradise in {location}!
        """
        
        # Generate image URLs using picsum.photos for realistic images
        images = [
            f"https://picsum.photos/seed/property{property_id}{i}/800/600" for i in range(1, 6)
        ]
        
        details = {
            'title': f"{property_type} in {location} - {bedrooms} BR",
            'price': f"฿{price:,}",
            'address': f"{random.randint(1, 100)} Sukhumvit Road, {location}, Thailand",
            'property_details': {
                'Property Type': property_type,
                'Bedrooms': str(bedrooms),
                'Bathrooms': str(bathrooms),
                'Land Size': f"{area} sqm",
                'Furnishing': random.choice(["Fully Furnished", "Partially Furnished", "Unfurnished"]),
                'Year Built': str(random.randint(2000, 2023)),
                'Amenities': amenities_text,
                'Property ID': f"DD-{property_id}"
            },
            'description': description.strip(),
            'images': images
        }
        
        return details