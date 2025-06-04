import os
import sys

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.app import app

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 12000))
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=True)