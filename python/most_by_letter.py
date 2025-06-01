from __future__ import print_function
import argparse
from collections import Counter
from appsheet_utils import get_appsheet_data, filter_data_by_year, get_band_equivalents

parser = argparse.ArgumentParser()
parser.add_argument('--year', type=int, default=-1, 
                    help='optional year to calculate')
args = parser.parse_args()

def main():
    """Shows bands seen most frequently by first letter."""
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

        most_by_letter = {}
        for band, cnt in bands.most_common():
            letter = band.replace('The ', '')[0].capitalize()
            if not letter.isalpha():
                continue
            
            if letter not in most_by_letter:
                most_by_letter[letter] = [(band, cnt)]
            elif len(most_by_letter[letter]) > 0 and most_by_letter[letter][0][1] == cnt:
                most_by_letter[letter] += [(band, cnt)]

        for letter in sorted(most_by_letter.keys()):
            for bcs in most_by_letter[letter]:
                print('%s - %s' % (letter, bcs))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
