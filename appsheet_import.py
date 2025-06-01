import json
import requests
import argparse
from datetime import datetime
from appsheet_utils import get_appsheet_data, get_band_equivalents, get_venues_data
import threading

class AppSheetImporter:
    def __init__(self, app_id, access_key):
        self.app_id = app_id
        self.access_key = access_key
        self.base_url = f"https://api.appsheet.com/api/v2/apps/{app_id}/tables"
        self.headers = {
            "Content-Type": "application/json",
            "ApplicationAccessKey": access_key
        }
    
    def _make_request(self, endpoint, method="GET", data=None):
        """Make a request to the AppSheet API."""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, json=data)
            response.raise_for_status()
            try:
                return response.json()
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON response: {e}")
                print(f"Response status code: {response.status_code}")
                print(f"Response headers: {response.headers}")
                print(f"Response content: {response.text}")
                raise
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status code: {e.response.status_code}")
                print(f"Response headers: {e.response.headers}")
                print(f"Response content: {e.response.text}")
            raise
    
    def get_table_schema(self, table_name):
        """Get the schema for a table."""
        data = {
            "Action": "GetSchema",
            "Properties": {
                "Locale": "en-US"
            }
        }
        return self._make_request(f"{table_name}/schema", "POST", data)
    
    def _validate_row(self, row, required_fields):
        """Validate that a row has all required fields and they're not empty."""
        for field in required_fields:
            if field not in row or row[field] is None or row[field] == '':
                raise ValueError(f"Missing required field '{field}' in row: {row}")
        return True

    def add_rows(self, table_name, rows):
        """Add rows to a table."""
        if not rows:
            print(f"Warning: No rows to add to {table_name}")
            return None

        print(f"Adding {len(rows)} rows to {table_name}...")

        # Validate each row
        required_fields = {
            'Band_Groups': ['PrimaryBand'],
            'Bands': ['Name'],
            'VenueList': ['Name', 'Location'],
            'Events': ['Name'],
            'Attendees': ['Name'],
            'ShowList': ['Date', 'VenueID'],
            'Show_Bands': ['ShowID', 'BandID', 'Order'],
            'Show_Attendees': ['ShowID', 'AttendeeID']
        }

        for row in rows:
            self._validate_row(row, required_fields.get(table_name, []))

        # AppSheet API expects rows in a specific format
        data = {
            "Action": "Add",
            "Properties": {
                "Locale": "en-US"
            },
            "Rows": rows
        }
        result = self._make_request(f"{table_name}/data", "POST", data)
        print(f"Successfully added {len(rows)} rows to {table_name}")
        return result
    
    def get_rows(self, table_name):
        """Get all rows from a table."""
        print(f"Fetching rows from {table_name}...")
        data = {
            "Action": "Find",
            "Properties": {
                "Locale": "en-US"
            },
            "Rows": []  # Empty to get all rows
        }
        result = self._make_request(f"{table_name}/data", "POST", data)
        # Handle both list and dict responses
        if isinstance(result, list):
            print(f"Retrieved {len(result)} rows from {table_name}")
            return {"Rows": result}
        elif isinstance(result, dict) and "Rows" in result:
            print(f"Retrieved {len(result['Rows'])} rows from {table_name}")
            return result
        else:
            print(f"Unexpected response format from {table_name}: {result}")
            return {"Rows": []}
    
    def import_band_groups(self, only_new_rows=False):
        """Import band groups data."""
        print("\nImporting Band_Groups...")
        data = []
        equivs = get_band_equivalents()
        primary_bands = set(equivs.values())
        
        if only_new_rows:
            existing_rows = self.get_rows("Band_Groups")
            existing_bands = {row["PrimaryBand"] for row in existing_rows["Rows"]}
            primary_bands = primary_bands - existing_bands
        
        for band in sorted(primary_bands):
            data.append({"PrimaryBand": band})
        
        print(f"Found {len(data)} unique band groups to import")
        return self.add_rows("Band_Groups", data)
    
    def import_bands(self, only_new_rows=False):
        """Import bands data."""
        print("\nImporting Bands...")
        # First get the band groups to map names to IDs
        band_groups = self.get_rows("Band_Groups")
        print(f"DEBUG: Band_Groups rows: {band_groups['Rows']}")  # Debug print
        band_groups_dict = {row["PrimaryBand"]: row["Row ID"] for row in band_groups["Rows"]}
        
        data = []
        equivs = get_band_equivalents()
        all_bands = set()
        for row in get_appsheet_data():
            if 'Bands' in row:
                all_bands.update(band.strip() for band in row['Bands'].split(','))
        
        for band in sorted(all_bands):
            primary_band = equivs.get(band, band)
            group_id = band_groups_dict.get(primary_band)
            data.append({
                "Name": band,
                "GroupID": group_id
            })
        
        print(f"Found {len(data)} unique bands to import")
        return self.add_rows("Bands", data)
    
    def import_venues(self, only_new_rows=False):
        """Import venues data."""
        print("\nImporting VenueList...")
        data = []
        venues_data = get_venues_data()
        
        if only_new_rows:
            existing_rows = self.get_rows("VenueList")
            existing_venues = {row["Name"] for row in existing_rows["Rows"]}
            venues_data = [row for row in venues_data if row.get('Name', '').strip() not in existing_venues]
        
        for row in venues_data:
            venue = row.get('Name', '').strip()
            location = row.get('Location', '').strip()
            closed = row.get('Closed', False)
            if venue and location:
                data.append({
                    "Name": venue,
                    "Location": location,
                    "Closed": closed
                })
        
        print(f"Found {len(data)} venues to import")
        return self.add_rows("VenueList", data)
    
    def import_events(self, only_new_rows=False):
        """Import events data."""
        print("\nImporting Events...")
        data = []
        events = set()
        for row in get_appsheet_data():
            if 'Event' in row and row['Event']:
                events.add(row['Event'].strip())
        
        if only_new_rows:
            existing_rows = self.get_rows("Events")
            existing_events = {row["Name"] for row in existing_rows["Rows"]}
            events = events - existing_events
        
        for event in sorted(events):
            data.append({"Name": event})
        
        print(f"Found {len(data)} events to import")
        return self.add_rows("Events", data)
    
    def import_attendees(self, only_new_rows=False):
        """Import attendees data."""
        print("\nImporting Attendees...")
        data = [{"Name": "Sarah"}]
        print("Adding 1 attendee (Sarah)")
        return self.add_rows("Attendees", data)
    
    def import_shows(self, only_new_rows=False):
        """Import shows data."""
        print("\nImporting ShowList...")
        # Get the venue and event mappings
        venues = self.get_rows("VenueList")
        venues_dict = {row["Name"]: row["Row ID"] for row in venues["Rows"]}
        
        events = self.get_rows("Events")
        events_dict = {row["Name"]: row["Row ID"] for row in events["Rows"]}
        
        data = []
        skipped = 0
        for row in get_appsheet_data():
            venue_name = row.get('Venue', '').strip()
            event_name = row.get('Event', '').strip()
            venue_id = venues_dict.get(venue_name)
            event_id = events_dict.get(event_name)
            
            if venue_id:  # Only add shows with valid venues
                try:
                    # Validate date format
                    date_str = row.get('Date', '')
                    if date_str:
                        datetime.strptime(date_str, '%m/%d/%Y')
                    
                    data.append({
                        "Date": date_str,
                        "VenueID": venue_id,
                        "Confirmed": bool(row.get('Confirmed', False)),
                        "EventID": event_id
                    })
                except ValueError as e:
                    print(f"Warning: Invalid date format for show: {row.get('Date')} - {e}")
                    print(f"Row data: {row}")
                    skipped += 1
                    continue
            else:
                print(f"Warning: Invalid venue for show: {venue_name}")
                print(f"Row data: {row}")
                skipped += 1
        
        if only_new_rows:
            existing_rows = self.get_rows("ShowList")
            existing_shows = {(row["Date"], row["VenueID"]) for row in existing_rows["Rows"]}
            data = [row for row in data if (row["Date"], row["VenueID"]) not in existing_shows]
        
        print(f"Found {len(data)} shows to import (skipped {skipped} invalid shows)")
        return self.add_rows("ShowList", data)
    
    def import_show_bands(self, only_new_rows=False):
        """Import show bands data."""
        print("\nImporting Show_Bands...")
        # Get the band and show mappings
        bands = self.get_rows("Bands")
        bands_dict = {row["Name"]: row["Row ID"] for row in bands["Rows"]}
        
        shows = self.get_rows("ShowList")
        shows_dict = {row["Date"]: row["Row ID"] for row in shows["Rows"]}
        
        data = []
        skipped = 0
        for row in get_appsheet_data():
            if 'Bands' in row:
                show_id = shows_dict.get(row.get('Date', ''))
                if show_id:
                    for order, band in enumerate(row['Bands'].strip().split(','), 1):
                        band = band.strip()
                        if band in bands_dict:
                            data.append({
                                "ShowID": show_id,
                                "BandID": bands_dict[band],
                                "Order": order
                            })
                        else:
                            skipped += 1
                else:
                    skipped += 1
        
        if only_new_rows:
            existing_rows = self.get_rows("Show_Bands")
            existing_show_bands = {(row["ShowID"], row["BandID"]) for row in existing_rows["Rows"]}
            data = [row for row in data if (row["ShowID"], row["BandID"]) not in existing_show_bands]
        
        print(f"Found {len(data)} show-band relationships to import (skipped {skipped} invalid relationships)")
        return self.add_rows("Show_Bands", data)
    
    def import_show_attendees(self, only_new_rows=False):
        """Import show attendees data."""
        print("\nImporting Show_Attendees...")
        # Get the attendee and show mappings
        attendees = self.get_rows("Attendees")
        attendee_id = next(row["Row ID"] for row in attendees["Rows"] if row["Name"] == "Sarah")
        
        shows = self.get_rows("ShowList")
        shows_dict = {row["Date"]: row["Row ID"] for row in shows["Rows"]}
        
        data = []
        skipped = 0
        for row in get_appsheet_data():
            if row.get('Sarah', False):
                show_id = shows_dict.get(row.get('Date', ''))
                if show_id:
                    data.append({
                        "ShowID": show_id,
                        "AttendeeID": attendee_id
                    })
                else:
                    skipped += 1
        
        if only_new_rows:
            existing_rows = self.get_rows("Show_Attendees")
            existing_show_attendees = {(row["ShowID"], row["AttendeeID"]) for row in existing_rows["Rows"]}
            data = [row for row in data if (row["ShowID"], row["AttendeeID"]) not in existing_show_attendees]
        
        print(f"Found {len(data)} show-attendee relationships to import (skipped {skipped} invalid relationships)")
        return self.add_rows("Show_Attendees", data)
    
    def import_all(self, only_new_rows=False):
        """Import all data in the correct order."""
        try:
            print("\nStarting data import process...")
            
            # Import parent tables first
            print("\n=== Importing Parent Tables ===")
            self.import_band_groups(only_new_rows)
            self.import_venues(only_new_rows)
            self.import_events(only_new_rows)
            self.import_attendees(only_new_rows)
            
            # Import child tables
            print("\n=== Importing Child Tables ===")
            self.import_bands(only_new_rows)
            self.import_shows(only_new_rows)
            self.import_show_bands(only_new_rows)
            self.import_show_attendees(only_new_rows)
            
            print("\n=== Import Complete ===")
            print("All data imported successfully!")
            
        except Exception as e:
            print(f"\nError during import: {e}")
            raise

    def test_connection(self):
        """Test the API connection by fetching rows from Band_Groups."""
        try:
            print("\nTesting API connection...")
            # Try to fetch rows from Band_Groups
            self.get_rows("Band_Groups")
            print("API connection successful!")
            return True
        except Exception as e:
            print(f"API connection failed: {e}")
            return False

    def delete_all_rows(self, table_name):
        """Delete all rows from a table in concurrent batches."""
        print(f"\nDeleting all rows from {table_name}...")
        try:
            # First get all rows
            rows = self.get_rows(table_name)
            if not rows.get("Rows"):
                print(f"No rows to delete in {table_name}")
                return

            # Delete rows in concurrent batches if more than 100 rows
            total_rows = len(rows["Rows"])
            if total_rows > 100:
                batch_size = 100
                threads = []
                for i in range(0, total_rows, batch_size):
                    batch = rows["Rows"][i:i + batch_size]
                    thread = threading.Thread(target=self._delete_batch, args=(table_name, batch, i//batch_size + 1, (total_rows + batch_size - 1)//batch_size))
                    threads.append(thread)
                    thread.start()
                for thread in threads:
                    thread.join()
                print(f"Successfully deleted all {total_rows} rows from {table_name}")
            else:
                # Delete all rows at once if less than 100
                data = {
                    "Action": "Delete",
                    "Properties": {
                        "Locale": "en-US"
                    },
                    "Rows": rows["Rows"]
                }
                self._make_request(f"{table_name}/data", "POST", data)
                print(f"Successfully deleted {total_rows} rows from {table_name}")
        except Exception as e:
            print(f"Error deleting rows from {table_name}: {e}")
            raise

    def _delete_batch(self, table_name, batch, batch_num, total_batches):
        """Helper method to delete a batch of rows."""
        data = {
            "Action": "Delete",
            "Properties": {
                "Locale": "en-US"
            },
            "Rows": batch
        }
        self._make_request(f"{table_name}/data", "POST", data)
        print(f"Deleted {len(batch)} rows from {table_name} (batch {batch_num}/{total_batches})")

    def wipe_all_data(self):
        """Delete all data from all tables in the correct order."""
        print("\n=== Wiping All Existing Data ===")
        
        # Delete from child tables first
        child_tables = [
            "Show_Attendees",
            "Show_Bands",
            "ShowList",
            "Bands",
            "Attendees",
            "Events",
            "VenueList",
            "Band_Groups"
        ]
        
        for table in child_tables:
            self.delete_all_rows(table)
        
        print("\nAll data wiped successfully!")

def main():
    """Import data into AppSheet using the API."""
    parser = argparse.ArgumentParser(description='Import data into AppSheet')
    parser.add_argument('--wipe', action='store_true', help='Wipe all existing data before import')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt and proceed')
    args = parser.parse_args()

    try:
        # Import credentials from local.py
        from config.local import APP_ID, ACCESS_KEY
        
        if not APP_ID or not ACCESS_KEY:
            print("Error: App ID and Access Key are required")
            return
        
        importer = AppSheetImporter(APP_ID, ACCESS_KEY)
        
        # Test the connection first
        if not importer.test_connection():
            print("Failed to connect to AppSheet API. Please check your App ID and Access Key.")
            return
        
        # Confirm before proceeding
        print("\nReady to import data. This will:")
        if args.wipe:
            print("1. WIPE ALL EXISTING DATA from all tables")
        print("1. Import parent tables (Band_Groups, VenueList, Events, Attendees)")
        print("2. Import child tables (Bands, ShowList, Show_Bands, Show_Attendees)")
        print("3. Set up all relationships using AppSheet's native _RowID")
        
        if not args.yes:
            confirm = input("\nDo you want to proceed? (y/N): ").strip().lower()
            if confirm != 'y':
                print("Import cancelled.")
                return
        else:
            print("Proceeding without confirmation (--yes flag set)")
        
        if args.wipe:
            importer.wipe_all_data()
        
        importer.import_all()
        
    except KeyboardInterrupt:
        print("\nImport cancelled by user.")
    except Exception as e:
        print(f"\nError during import: {e}")
        raise

if __name__ == '__main__':
    main() 