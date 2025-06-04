# DDProperty Real Estate Scraper

This application collects and groups real estate properties from ddproperty.com by specified categories.

## Features

- Search for properties on ddproperty.com with various filters
- Group properties by location, bedrooms, bathrooms, or price range
- View detailed information about each property
- Save search results and grouped data to JSON files

## Requirements

- Python 3.8+
- Chrome browser (for Selenium WebDriver)
- Required Python packages (see requirements.txt)

## Installation

1. Clone this repository:
```
git clone https://github.com/yourusername/ddproperty-scraper.git
cd ddproperty-scraper
```

2. Install the required packages:
```
pip install -r requirements.txt
```

## Usage

1. Run the application:
```
python main.py
```

2. Open your web browser and navigate to:
```
http://localhost:12000
```

3. Use the search form to find properties based on your criteria.

4. View the search results and group them by different categories.

## API Endpoints

The application also provides API endpoints for programmatic access:

- `POST /api/search` - Search for properties
  - Request body: JSON object with search parameters
  - Response: JSON array of property objects

- `POST /api/group` - Group properties by category
  - Request body: JSON object with properties array and category
  - Response: JSON object with grouped properties

## Data Storage

All search results and grouped data are stored in the `data` directory as JSON files.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This application is for educational purposes only. Please respect ddproperty.com's terms of service and robots.txt when using this application.