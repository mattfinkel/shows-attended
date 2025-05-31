from __future__ import print_function
import argparse
from collections import Counter
from appsheet_utils import get_appsheet_data, filter_data_by_year, get_band_equivalents

parser = argparse.ArgumentParser()
parser.add_argument('--year', type=int, default=-1, 
                    help='optional year to calculate')
parser.add_argument('--limit', type=int, default=-1,
                    help='optional limit on number of results to show')
args = parser.parse_args()

def main():
    """Fetches data from AppSheet and counts band appearances."""
    try:
        data = get_appsheet_data()
        
        if not data:
            print('No data found.')
            return

        # Filter by year if specified
        data = filter_data_by_year(data, args.year)

        bands = Counter()
        equivs = get_band_equivalents()
        
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

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
