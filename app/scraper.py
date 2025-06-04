import time
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DDPropertyScraper:
    def __init__(self):
        self.base_url = "https://www.ddproperty.com"
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1920,1080")
        
    def setup_driver(self):
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=self.chrome_options)
            return driver
        except Exception as e:
            logger.error(f"Error setting up WebDriver: {e}")
            return None
            
    def search_properties(self, search_params):
        """
        Search for properties based on given parameters
        
        search_params: dict with keys like 'location', 'property_type', 'price_min', 'price_max', etc.
        """
        driver = self.setup_driver()
        if not driver:
            return []
            
        try:
            # Construct search URL based on parameters
            search_url = self._build_search_url(search_params)
            logger.info(f"Searching with URL: {search_url}")
            
            driver.get(search_url)
            time.sleep(5)  # Allow page to load
            
            # Wait for property listings to appear
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.ListingsListstyle__ListingListContainer-srp__sc-i2mz0b-0"))
            )
            
            # Get the page source and parse with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Extract property listings
            properties = self._extract_properties(soup)
            
            # Check if there are more pages
            total_pages = self._get_total_pages(soup)
            current_page = 1
            
            # Scrape additional pages if available (limit to 5 pages for demo)
            while current_page < min(total_pages, 5):
                current_page += 1
                next_page_url = f"{search_url}&page={current_page}"
                logger.info(f"Scraping page {current_page} of {total_pages}")
                
                driver.get(next_page_url)
                time.sleep(3)  # Allow page to load
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                page_properties = self._extract_properties(soup)
                properties.extend(page_properties)
            
            return properties
            
        except Exception as e:
            logger.error(f"Error during property search: {e}")
            return []
        finally:
            driver.quit()
    
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
            
    def get_property_details(self, property_url):
        """Get detailed information about a specific property"""
        driver = self.setup_driver()
        if not driver:
            return {}
            
        try:
            driver.get(property_url)
            time.sleep(5)  # Allow page to load
            
            # Wait for property details to appear
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.DetailsSectionstyle__DetailsContainer-srp__sc-1gv43ito-0"))
            )
            
            # Get the page source and parse with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Extract detailed property information
            details = {}
            
            # Title
            title_elem = soup.select_one("h1.PropertyDetailsstyle__TitleWrapper-srp__sc-1dj5kkj-2")
            details['title'] = title_elem.text.strip() if title_elem else "No title"
            
            # Price
            price_elem = soup.select_one("div.PricingInfostyle__PriceContainer-srp__sc-19c7c2f-0 span")
            details['price'] = price_elem.text.strip() if price_elem else "Price not specified"
            
            # Address
            address_elem = soup.select_one("span.PropertyDetailsstyle__Address-srp__sc-1dj5kkj-3")
            details['address'] = address_elem.text.strip() if address_elem else "Address not specified"
            
            # Property details
            property_details = {}
            detail_sections = soup.select("div.DetailsSectionstyle__DetailsContainer-srp__sc-1gv43ito-0")
            
            for section in detail_sections:
                section_title_elem = section.select_one("h2")
                if not section_title_elem:
                    continue
                    
                section_title = section_title_elem.text.strip()
                
                if section_title == "Property Details":
                    detail_items = section.select("div.KeyInfosectionstyle__KeyInfoContainer-srp__sc-jkxicn-0")
                    for item in detail_items:
                        label_elem = item.select_one("div.KeyInfosectionstyle__Label-srp__sc-jkxicn-1")
                        value_elem = item.select_one("div.KeyInfosectionstyle__Value-srp__sc-jkxicn-2")
                        
                        if label_elem and value_elem:
                            label = label_elem.text.strip()
                            value = value_elem.text.strip()
                            property_details[label] = value
            
            details['property_details'] = property_details
            
            # Description
            description_elem = soup.select_one("div.PropertyDescriptionstyle__PropertyDescriptionContainer-srp__sc-1cz8d8w-0 p")
            details['description'] = description_elem.text.strip() if description_elem else "No description available"
            
            # Images
            image_elems = soup.select("div.GallerySliderstyle__GalleryContainer-srp__sc-1t5vfh0-0 img")
            details['images'] = [img['src'] for img in image_elems if 'src' in img.attrs]
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting property details: {e}")
            return {}
        finally:
            driver.quit()
            
    def group_properties_by_category(self, properties, category):
        """Group properties by a specific category"""
        if not properties:
            return {}
            
        # Convert to DataFrame for easier grouping
        df = pd.DataFrame(properties)
        
        # Group by the specified category
        if category in df.columns:
            grouped = df.groupby(category).apply(lambda x: x.to_dict('records')).to_dict()
            return grouped
        else:
            logger.error(f"Category '{category}' not found in property data")
            return {}
            
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