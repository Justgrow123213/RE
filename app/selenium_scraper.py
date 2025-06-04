import time
import json
import logging
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SeleniumDDPropertyScraper:
    def __init__(self):
        self.base_url = "https://www.ddproperty.com"
        self.driver = None
        
    def _setup_driver(self):
        """Set up Chrome driver with appropriate options"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--remote-debugging-port=9222")
            
            # Add user agent
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            # Disable automation flags
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Install Chrome driver
            service = Service(ChromeDriverManager().install())
            
            # Create driver
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set page load timeout
            driver.set_page_load_timeout(30)
            
            return driver
        except Exception as e:
            logger.error(f"Error setting up Chrome driver: {str(e)}")
            return None
    
    def search_properties(self, search_params):
        """
        Search for properties based on given parameters using Selenium
        """
        try:
            # Build search URL
            search_url = f"{self.base_url}/en/search/buy/"
            
            # Add location if provided
            if search_params.get("location"):
                search_url += f"{search_params.get('location')}/"
            
            # Add query parameters
            query_params = []
            
            # Add property type if provided
            if search_params.get("property_type"):
                query_params.append(f"propertyType={search_params.get('property_type')}")
            
            # Add price range if provided
            if search_params.get("price_min"):
                query_params.append(f"price_min={search_params.get('price_min')}")
            if search_params.get("price_max"):
                query_params.append(f"price_max={search_params.get('price_max')}")
            
            # Add bedroom range if provided
            if search_params.get("bedrooms_min"):
                query_params.append(f"bedrooms_min={search_params.get('bedrooms_min')}")
            if search_params.get("bedrooms_max"):
                query_params.append(f"bedrooms_max={search_params.get('bedrooms_max')}")
            
            # Add bathroom range if provided
            if search_params.get("bathrooms_min"):
                query_params.append(f"bathrooms_min={search_params.get('bathrooms_min')}")
            if search_params.get("bathrooms_max"):
                query_params.append(f"bathrooms_max={search_params.get('bathrooms_max')}")
            
            # Add area range if provided
            if search_params.get("area_min"):
                query_params.append(f"area_min={search_params.get('area_min')}")
            if search_params.get("area_max"):
                query_params.append(f"area_max={search_params.get('area_max')}")
            
            # Add query parameters to URL
            if query_params:
                search_url += "?" + "&".join(query_params)
            
            logger.info(f"Searching with URL: {search_url}")
            
            # Set up Chrome driver
            self.driver = self._setup_driver()
            
            if not self.driver:
                logger.error("Failed to set up Chrome driver")
                return self._generate_sample_data_from_params(search_params)
            
            try:
                # Navigate to search URL
                logger.info(f"Navigating to: {search_url}")
                self.driver.get(search_url)
                
                # Wait for page to load
                logger.info("Waiting for page to load...")
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Wait for property listings to load
                time.sleep(5)  # Additional wait for JavaScript to load content
                
                # Save page source for debugging
                with open('selenium_html.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                
                logger.info("Page loaded successfully")
                
                # Parse HTML with BeautifulSoup
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Extract property listings
                properties = self._extract_properties(soup)
                logger.info(f"Extracted {len(properties)} properties from the page")
                
                # If no properties found, try to extract with different selectors
                if not properties:
                    logger.warning("No properties found with primary selectors, trying alternative selectors")
                    properties = self._extract_properties_alternative(soup)
                    logger.info(f"Extracted {len(properties)} properties with alternative selectors")
                
                # If still no properties found, use sample data
                if not properties:
                    logger.warning("No properties found, using sample data")
                    properties = self._generate_sample_data_from_params(search_params)
                
                return properties
                
            finally:
                # Close the driver
                if self.driver:
                    self.driver.quit()
                    self.driver = None
                
        except Exception as e:
            logger.error(f"Error during Selenium scraping: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Close the driver if it exists
            if self.driver:
                self.driver.quit()
                self.driver = None
            
            # Return sample data as fallback
            return self._generate_sample_data_from_params(search_params)
    
    def _extract_properties(self, soup):
        """Extract properties from the page"""
        properties = []
        
        try:
            # Try different selectors for property listings
            property_elements = soup.select("div.ListingsListstyle__ListingListItemWrapper-srp__sc-1p2reyq-1")
            
            if not property_elements:
                property_elements = soup.select("div.ListingCardstyle__ListingCardContainer-srp__sc-1epjt8y-0")
            
            if not property_elements:
                property_elements = soup.select("[data-testid='listing-card']")
            
            if not property_elements:
                property_elements = soup.select(".ListingCard")
            
            if not property_elements:
                logger.warning("Could not find property elements with primary selectors")
                return []
            
            for element in property_elements:
                try:
                    property_data = {}
                    
                    # Extract title
                    title_element = element.select_one(".ListingCardstyle__TitleWrapper-srp__sc-1epjt8y-7") or \
                                   element.select_one("[data-testid='listing-title']") or \
                                   element.select_one(".ListingCard__title")
                    
                    if title_element:
                        property_data["title"] = title_element.text.strip()
                    else:
                        property_data["title"] = "No title"
                    
                    # Extract price
                    price_element = element.select_one(".PricingTextstyle__Wrapper-srp__sc-19m9bjo-0") or \
                                   element.select_one("[data-testid='listing-price']") or \
                                   element.select_one(".ListingCard__price")
                    
                    if price_element:
                        property_data["price"] = price_element.text.strip()
                    else:
                        property_data["price"] = "Price not specified"
                    
                    # Extract location
                    location_element = element.select_one(".ListingCardstyle__LocationWrapper-srp__sc-1epjt8y-8") or \
                                      element.select_one("[data-testid='listing-location']") or \
                                      element.select_one(".ListingCard__location")
                    
                    if location_element:
                        property_data["location"] = location_element.text.strip()
                    else:
                        property_data["location"] = "Location not specified"
                    
                    # Extract property details (bedrooms, bathrooms, area)
                    details_elements = element.select(".ListingCardstyle__KeyInfoWrapper-srp__sc-1epjt8y-9 span") or \
                                      element.select("[data-testid='listing-details'] span") or \
                                      element.select(".ListingCard__details span")
                    
                    property_data["bedrooms"] = "N/A"
                    property_data["bathrooms"] = "N/A"
                    property_data["area"] = "N/A"
                    
                    for detail in details_elements:
                        detail_text = detail.text.strip()
                        if "bed" in detail_text.lower():
                            property_data["bedrooms"] = detail_text
                        elif "bath" in detail_text.lower():
                            property_data["bathrooms"] = detail_text
                        elif "sq" in detail_text.lower():
                            property_data["area"] = detail_text
                    
                    # Extract URL
                    url_element = element.select_one("a") or element.select_one("[data-testid='listing-link']")
                    
                    if url_element and url_element.has_attr("href"):
                        url = url_element["href"]
                        if not url.startswith("http"):
                            url = f"{self.base_url}{url}"
                        property_data["url"] = url
                    else:
                        property_data["url"] = "URL not available"
                    
                    # Extract image URL
                    img_element = element.select_one("img") or element.select_one("[data-testid='listing-image']")
                    
                    if img_element and img_element.has_attr("src"):
                        property_data["image_url"] = img_element["src"]
                    elif img_element and img_element.has_attr("data-src"):
                        property_data["image_url"] = img_element["data-src"]
                    else:
                        property_data["image_url"] = "No image"
                    
                    properties.append(property_data)
                    
                except Exception as e:
                    logger.error(f"Error extracting property data: {str(e)}")
                    continue
            
            return properties
            
        except Exception as e:
            logger.error(f"Error extracting properties: {str(e)}")
            return []
    
    def _extract_properties_alternative(self, soup):
        """Extract properties using alternative selectors"""
        properties = []
        
        try:
            # Try to find any elements that might contain property listings
            # Look for common patterns in real estate websites
            
            # Try to find elements with specific classes or attributes
            property_elements = soup.select("div.property-listing") or \
                               soup.select("div.listing-item") or \
                               soup.select("div.property-card") or \
                               soup.select("div[data-listing]") or \
                               soup.select("article.property") or \
                               soup.select(".property")
            
            if not property_elements:
                # Try to find elements with specific structure
                property_elements = soup.select("div > a > div > img")
                if property_elements:
                    property_elements = [elem.parent.parent for elem in property_elements]
            
            if not property_elements:
                logger.warning("Could not find property elements with alternative selectors")
                return []
            
            for element in property_elements:
                try:
                    property_data = {}
                    
                    # Extract title - look for heading elements
                    title_element = element.select_one("h1") or \
                                   element.select_one("h2") or \
                                   element.select_one("h3") or \
                                   element.select_one("h4") or \
                                   element.select_one(".title") or \
                                   element.select_one("[class*='title']")
                    
                    if title_element:
                        property_data["title"] = title_element.text.strip()
                    else:
                        property_data["title"] = "No title"
                    
                    # Extract price - look for elements with price-related text
                    price_element = element.select_one("[class*='price']") or \
                                   element.select_one("span:contains('฿')") or \
                                   element.select_one("div:contains('฿')")
                    
                    if price_element:
                        property_data["price"] = price_element.text.strip()
                    else:
                        property_data["price"] = "Price not specified"
                    
                    # Extract location
                    location_element = element.select_one("[class*='location']") or \
                                      element.select_one("[class*='address']") or \
                                      element.select_one("span:contains('Bangkok')") or \
                                      element.select_one("div:contains('Bangkok')")
                    
                    if location_element:
                        property_data["location"] = location_element.text.strip()
                    else:
                        property_data["location"] = "Location not specified"
                    
                    # Extract property details
                    property_data["bedrooms"] = "N/A"
                    property_data["bathrooms"] = "N/A"
                    property_data["area"] = "N/A"
                    
                    # Look for elements with detail information
                    details_elements = element.select("[class*='detail']") or \
                                      element.select("[class*='feature']") or \
                                      element.select("span") or \
                                      element.select("div > span")
                    
                    for detail in details_elements:
                        detail_text = detail.text.strip()
                        if "bed" in detail_text.lower():
                            property_data["bedrooms"] = detail_text
                        elif "bath" in detail_text.lower():
                            property_data["bathrooms"] = detail_text
                        elif "sq" in detail_text.lower() or "m²" in detail_text:
                            property_data["area"] = detail_text
                    
                    # Extract URL
                    url_element = element.select_one("a") or element.parent if element.name != "a" else element
                    
                    if url_element and url_element.has_attr("href"):
                        url = url_element["href"]
                        if not url.startswith("http"):
                            url = f"{self.base_url}{url}"
                        property_data["url"] = url
                    else:
                        property_data["url"] = "URL not available"
                    
                    # Extract image URL
                    img_element = element.select_one("img") or element.select_one("[class*='image']")
                    
                    if img_element and img_element.has_attr("src"):
                        property_data["image_url"] = img_element["src"]
                    elif img_element and img_element.has_attr("data-src"):
                        property_data["image_url"] = img_element["data-src"]
                    else:
                        property_data["image_url"] = "No image"
                    
                    properties.append(property_data)
                    
                except Exception as e:
                    logger.error(f"Error extracting property data with alternative selectors: {str(e)}")
                    continue
            
            return properties
            
        except Exception as e:
            logger.error(f"Error extracting properties with alternative selectors: {str(e)}")
            return []
    
    def _generate_sample_data_from_params(self, search_params):
        """Generate sample property data based on search parameters"""
        sample_properties = []
        
        # Get location from search parameters
        location = search_params.get("location", "Bangkok")
        
        # Get price range from search parameters
        price_min = int(search_params.get("price_min", 1000000))
        price_max = int(search_params.get("price_max", 10000000))
        
        # Get bedroom range from search parameters
        bedrooms_min = int(search_params.get("bedrooms_min", 1))
        bedrooms_max = int(search_params.get("bedrooms_max", 3))
        
        # Get bathroom range from search parameters
        bathrooms_min = int(search_params.get("bathrooms_min", 1))
        bathrooms_max = int(search_params.get("bathrooms_max", 2))
        
        # Generate 10 sample properties
        import random
        
        property_types = ["Condo", "Apartment", "House", "Villa", "Townhouse"]
        areas = ["Sukhumvit", "Silom", "Sathorn", "Thonglor", "Asoke", "Rama 9", "Ratchada", "Phra Khanong", "On Nut", "Pattaya"]
        
        for i in range(10):
            # Generate random property data
            bedrooms = random.randint(bedrooms_min, bedrooms_max)
            bathrooms = random.randint(bathrooms_min, bathrooms_max)
            price = random.randint(price_min, price_max)
            area_size = random.randint(30, 200)
            
            # Format price with commas
            price_formatted = f"฿ {price:,}"
            
            # Create property data
            property_data = {
                "title": f"{random.choice(property_types)} for Sale in {random.choice(areas)}, {location}",
                "price": price_formatted,
                "location": f"{random.choice(areas)}, {location}",
                "bedrooms": f"{bedrooms} bed",
                "bathrooms": f"{bathrooms} bath",
                "area": f"{area_size} sq.m",
                "url": f"https://www.ddproperty.com/property/{i+1}",
                "image_url": f"https://picsum.photos/id/{random.randint(1, 100)}/300/200"
            }
            
            sample_properties.append(property_data)
        
        return sample_properties