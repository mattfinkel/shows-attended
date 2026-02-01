#!/usr/bin/env python3
import urllib.request
import urllib.error
import json

app_id = "b1595711-76c0-4fb1-a42c-5d7e060a2fc4"
access_key = "V2-bVJma-M1E3V-ULxcT-Hyoup-stc2n-wrtH3-Qviv9-uy2i8"

tables = ["Shows", "Venues", "Bands", "ShowBands"]

for table_name in tables:
    print(f"\n{'='*60}")
    print(f"Fetching: {table_name}")
    print(f"{'='*60}")

    url = f"https://api.appsheet.com/api/v2/apps/{app_id}/tables/{table_name}/Action"

    payload = {
        "Action": "Find",
        "Properties": {
            "Locale": "en-US"
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
        with urllib.request.urlopen(req, timeout=30) as response:
            response_bytes = response.read()

            if len(response_bytes) > 0:
                response_data = response_bytes.decode('utf-8')
                result = json.loads(response_data)

                filename = f"data_{table_name.lower()}.json"
                with open(filename, "w") as f:
                    json.dump(result, f, indent=2)

                if isinstance(result, list):
                    print(f"✓ Saved {len(result)} rows to {filename}")
                    if len(result) > 0:
                        print(f"  Columns: {', '.join(result[0].keys())}")
                        print(f"  First row sample:")
                        for key, value in list(result[0].items())[:5]:
                            print(f"    {key}: {value}")
                else:
                    print(f"✓ Saved data to {filename}")

    except Exception as e:
        print(f"✗ Error: {e}")

print("\n" + "="*60)
print("Fetch complete!")
