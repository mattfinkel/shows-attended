#!/usr/bin/env python3
import urllib.request
import urllib.error
import json

app_id = "b1595711-76c0-4fb1-a42c-5d7e060a2fc4"
access_key = "V2-bVJma-M1E3V-ULxcT-Hyoup-stc2n-wrtH3-Qviv9-uy2i8"

url = f"https://api.appsheet.com/api/v2/apps/{app_id}/tables/Shows/Action"

# Try different actions
actions_to_try = [
    {
        "name": "Find with simple selector",
        "payload": {
            "Action": "Find",
            "Properties": {
                "Locale": "en-US",
                "Selector": "Select(Shows[ID], true)",
                "MaxRows": 5
            },
            "Rows": []
        }
    },
    {
        "name": "Find without selector",
        "payload": {
            "Action": "Find",
            "Properties": {
                "Locale": "en-US"
            },
            "Rows": []
        }
    }
]

for test in actions_to_try:
    print(f"\n{'='*60}")
    print(f"Testing: {test['name']}")
    print(f"{'='*60}")

    data = json.dumps(test['payload']).encode('utf-8')

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
            print(f"Status: {response.status}")

            if len(response_bytes) > 0:
                response_data = response_bytes.decode('utf-8')
                result = json.loads(response_data)

                print(f"Response type: {type(result)}")
                print(f"Response preview: {json.dumps(result, indent=2)[:1000]}")

                # Save successful response
                if isinstance(result, list) and len(result) > 0 and result[0].get('Date'):
                    filename = f"appsheet_shows_working.json"
                    with open(filename, "w") as f:
                        json.dump(result, f, indent=2)
                    print(f"\n✓ SUCCESS! Saved to {filename}")
                    break

    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        print(f"✗ HTTP Error {e.code}: {error_msg}")
    except Exception as e:
        print(f"✗ Error: {e}")
