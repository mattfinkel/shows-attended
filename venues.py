from __future__ import print_function
import argparse
from collections import Counter
from appsheet_utils import get_appsheet_data, filter_data_by_year

parser = argparse.ArgumentParser()
parser.add_argument('--year', type=int, default=-1, 
                    help='optional year to calculate')
parser.add_argument('--limit', type=int, default=-1,
                    help='optional limit on number of results to show')
args = parser.parse_args()

def main():
    """Fetches data from AppSheet and counts venue appearances."""
    try:
        data = get_appsheet_data()
        
        if not data:
            print('No data found.')
            return

        # Filter by year if specified
        data = filter_data_by_year(data, args.year)

        venues = Counter()
        
        for row in data:
            if 'Venue' in row and row['Venue']:
                venue = row['Venue'].strip()
                venues[venue] += 1

        # Sort by count (descending) and then by venue name (ascending)
        sorted_venues = sorted(venues.items(), key=lambda x: (-x[1], x[0]))
        
        # Apply limit if specified
        if args.limit > 0:
            sorted_venues = sorted_venues[:args.limit]
            
        for venue, cnt in sorted_venues:
            print('%s: %d' % (venue, cnt))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main() 