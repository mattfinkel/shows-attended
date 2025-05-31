import requests
import json
from datetime import datetime
from config import APP_ID, ACCESS_KEY

# AppSheet API configuration
TABLE_NAME = 'Shows'

# Common band name equivalents
EQUIVALENTS = [
    ("Lenny Lashley", "Lenny Lashley's Gang of One", "Lenny Lashley & Friends"),
    ("Frank Turner", "Frank Turner & the Sleeping Souls"),
    ("Chuck Ragan", "Chuck Ragan & The Camradarie")
]

def get_appsheet_data():
    """Fetches data from AppSheet API."""
    if not APP_ID or not ACCESS_KEY:
        raise ValueError("Please set APPSHEET_APP_ID and APPSHEET_ACCESS_KEY environment variables")

    headers = {
        'Authorization': f'Bearer {ACCESS_KEY}',
        'Content-Type': 'application/json',
        'ApplicationAccessKey': ACCESS_KEY
    }

    url = f'https://api.appsheet.com/api/v2/apps/{APP_ID}/tables/{TABLE_NAME}/Action'
    payload = {
        "Action": "Find",
        "Properties": {
            "Locale": "en-US",
            "Timezone": "UTC"
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    if not response.text:
        return []

    try:
        return response.json()
    except json.JSONDecodeError as e:
        raise ValueError(f"Error parsing JSON response: {e}")

def filter_data_by_year(data, year):
    """Filters AppSheet data by year."""
    if year == -1:
        return data
        
    filtered_data = []
    for row in data:
        try:
            date = datetime.strptime(row['Date'], '%m/%d/%Y')
            if date.year == year:
                filtered_data.append(row)
        except (ValueError, KeyError):
            continue
    return filtered_data

def get_band_equivalents():
    """Returns a dictionary mapping band name variations to their canonical form."""
    return dict([(val, row[0]) for row in EQUIVALENTS for val in row])

def normalize_band_name(band_name):
    """Normalizes a band name for comparison by removing common prefixes and special characters."""
    return band_name.lower().replace('the ', '').replace('and ', '').replace('& ', '').replace("'", '').replace('.', '').replace('!', '').replace(' ', '') 