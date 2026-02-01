#!/usr/bin/env python3
import urllib.request
import urllib.error
import json

app_id = "b1595711-76c0-4fb1-a42c-5d7e060a2fc4"
access_key = "V2-bVJma-M1E3V-ULxcT-Hyoup-stc2n-wrtH3-Qviv9-uy2i8"

tables = ["Shows", "Venues", "Bands", "ShowBands"]

for table_name in tables:
    print(f"\n{'='*60}")
    print(f"Fetching from table: {table_name}")
    print(f"{'='*60}")

    url = f"https://api.appsheet.com/api/v2/apps/{app_id}/tables/{table_name}/Action"

    # Try a simpler Find action
    payload = {
        "Action": "Find",
        "Properties": {
            "Locale": "en-US",
            "Selector": f"TOP(SELECT({table_name}[_RowNumber], TRUE), 5)"
        },
        "Rows": []
    }

    data = json.dumps(payload).encode('utf-8')

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "ApplicationAccessKey": access_key,
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            response_bytes = response.read()
            print(f"Status: {response.status}, Response length: {len(response_bytes)} bytes")

            if len(response_bytes) > 0:
                response_data = response_bytes.decode('utf-8')
                result = json.loads(response_data)

                # Save to file
                filename = f"appsheet_{table_name.lower()}.json"
                with open(filename, "w") as f:
                    json.dump(result, f, indent=2)

                # Handle both list and dict responses
                if isinstance(result, list):
                    rows = result
                elif isinstance(result, dict):
                    rows = result.get('Rows', [])
                else:
                    rows = []

                num_rows = len(rows)
                print(f"✓ Saved {num_rows} rows to {filename}")

                if num_rows > 0:
                    print(f"  Column names: {list(rows[0].keys())}")
                    print(f"  Sample row: {json.dumps(rows[0], indent=2)[:500]}")
            else:
                print("  Empty response")

    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        print(f"✗ HTTP Error {e.code}: {error_msg[:200]}")
    except Exception as e:
        print(f"✗ Error: {e}")

print("\n" + "="*60)
print("Done!")
