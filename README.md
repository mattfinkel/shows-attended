# Shows Attended

A system for tracking concerts and shows attended, with both Python scripts for data management and a Google Apps Script web interface for easy data entry.

## Project Structure

- `python/`: Python scripts for data management
  - `appsheet_import.py`: Script for importing data into AppSheet
  - `create_tables.py`: Script for creating AppSheet tables
  - `appsheet_utils.py`: Utilities for working with AppSheet data
  - `bands_seen.py`: Script for tracking bands seen at concerts
  - `venues.py`: Script for tracking and counting venues visited
  - `duplicates.py`: Script for finding duplicate entries
  - `most_by_letter.py`: Analysis of bands by letter frequency
  - `config/`: Configuration files
  - `requirements.txt`: Python dependencies

- `apps_script/`: Google Apps Script web interface
  - `Code.gs`: Main Apps Script code
  - `show_entry.html`: Web interface for adding new shows

## Setup

### Python Scripts
1. Install dependencies:
   ```bash
   cd python
   pip install -r requirements.txt
   ```

2. Configure AppSheet credentials in the scripts

### Google Apps Script
1. Create a new Apps Script project
2. Copy the contents of `apps_script/` files into the project
3. Set up Script Properties:
   - `APP_ID`: Your AppSheet App ID
   - `ACCESS_KEY`: Your AppSheet Access Key
4. Deploy as a web app

## Development

### Python Scripts
- Run scripts from the `python/` directory
- Example: `python appsheet_import.py --wipe --yes`

### Apps Script
- Make changes to files in `apps_script/`
- Changes will automatically sync and deploy via GitHub integration

## GitHub Integration
The Apps Script project is connected to this repository. Changes pushed to the `apps_script/` directory will automatically sync and deploy to the web app. 