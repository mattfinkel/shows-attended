#!/usr/bin/env python3
import urllib.request
import urllib.error
import json

app_id = "b1595711-76c0-4fb1-a42c-5d7e060a2fc4"
access_key = "V2-bVJma-M1E3V-ULxcT-Hyoup-stc2n-wrtH3-Qviv9-uy2i8"
table_name = "Shows"

url = f"https://api.appsheet.com/api/v2/apps/{app_id}/tables/{table_name}/Action"

# Try Find action with selector
payload = {
    "Action": "Find",
    "Properties": {
        "Locale": "en-US",
        "Selector": "Filter(Shows, true)",
        "MaxRows": 10
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

print("Sending request...")
try:
    with urllib.request.urlopen(req) as response:
        response_bytes = response.read()
        print(f"Status Code: {response.status}")
        print(f"Response length: {len(response_bytes)} bytes")
        print(f"Response bytes: {response_bytes[:200]}")

        if len(response_bytes) == 0:
            print("Empty response!")
        else:
            response_data = response_bytes.decode('utf-8')
            print(f"Response text: {response_data[:2000]}")

            result = json.loads(response_data)
            with open("appsheet_data.json", "w") as f:
                json.dump(result, f, indent=2)
            print(f"\nData saved to appsheet_data.json")
            print(f"Number of rows: {len(result.get('Rows', []))}")

            # Print first row structure
            if result.get('Rows'):
                print(f"\nFirst row keys: {list(result['Rows'][0].keys())}")

except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(f"Error message: {e.read().decode('utf-8')}")
except Exception as e:
    print(f"Error: {e}")
