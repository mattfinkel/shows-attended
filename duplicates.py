from __future__ import print_function
import argparse
from collections import defaultdict
from appsheet_utils import get_appsheet_data, normalize_band_name

parser = argparse.ArgumentParser()
parser.add_argument('--year', type=int, default=-1, 
                    help='optional year to calculate')
args = parser.parse_args()

def main():
    """Finds duplicate band names with different spellings."""
    try:
        data = get_appsheet_data()
        
        if not data:
            print('No data found.')
            return

        bands = defaultdict(set)
        for row in data:
            if 'Bands' in row:
                for band in row['Bands'].strip().split(", "):
                    key = normalize_band_name(band)
                    bands[key].add(band)

        for dups in bands.values():
            if len(dups) > 1:
                print(dups)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
