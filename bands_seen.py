from __future__ import print_function
import requests
from collections import Counter
import argparse
import os
import json
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument('--year', type=int, default=-1, 
                    help='optional year to calculate')
parser.add_argument('--limit', type=int, default=-1,
                    help='optional limit on number of results to show')
args = parser.parse_args()

# AppSheet API configuration
APP_ID = os.getenv('APPSHEET_APP_ID')  # Your AppSheet App ID
ACCESS_KEY = os.getenv('APPSHEET_ACCESS_KEY')  # Your AppSheet Application Access Key
TABLE_NAME = 'Shows'  # Your table name in AppSheet

EQUIVALENTS = [("Lenny Lashley", "Lenny Lashley's Gang of One", "Lenny Lashley & Friends"),
               ("Frank Turner", "Frank Turner & the Sleeping Souls"),
               ("Chuck Ragan", "Chuck Ragan & The Camradarie")]

def main():
    """Fetches data from AppSheet and counts band appearances."""
    if not APP_ID or not ACCESS_KEY:
        print("Error: Please set APPSHEET_APP_ID and APPSHEET_ACCESS_KEY environment variables")
        return

    headers = {
        'Authorization': f'Bearer {ACCESS_KEY}',
        'Content-Type': 'application/json',
        'ApplicationAccessKey': ACCESS_KEY
    }

    # Fetch data from AppSheet
    url = f'https://api.appsheet.com/api/v2/apps/{APP_ID}/tables/{TABLE_NAME}/Action'
    payload = {
        "Action": "Find",
        "Properties": {
            "Locale": "en-US",
            "Timezone": "UTC"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        if not response.text:
            print('No data found.')
            return

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return

        if not data:
            print('No data found.')
            return

        # Filter by year if specified
        if args.year != -1:
            filtered_data = []
            for row in data:
                try:
                    date = datetime.strptime(row['Date'], '%m/%d/%Y')
                    if date.year == args.year:
                        filtered_data.append(row)
                except (ValueError, KeyError):
                    continue
            data = filtered_data

        bands = Counter()
        equivs = dict([(val, row[0]) for row in EQUIVALENTS for val in row])
        
        for row in data:
            if 'Bands' in row:
                for band in row['Bands'].strip().split(", "):
                    key = equivs[band] if band in equivs else band
                    bands[key] += 1

        # Sort by count (descending) and then by band name (ascending)
        sorted_bands = sorted(bands.items(), key=lambda x: (-x[1], x[0]))
        
        # Apply limit if specified
        if args.limit > 0:
            sorted_bands = sorted_bands[:args.limit]
            
        for band, cnt in sorted_bands:
            print('%s: %d' % (band, cnt))

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from AppSheet: {e}")

if __name__ == '__main__':
    main()
