import requests
import json
import yaml
import os
import sys

# Paths and API URL
YAML_FILE = "~/Declaration-files/google-cloud/central-india/kafka/dev-iot.yaml"
JSON_FILE = os.path.splitext(os.path.basename(YAML_FILE))[0] + ".json"
API_URL = "https://sapient-duality-469110-d9.el.r.appspot.com/data"

def convert_yaml_to_json(yaml_path, json_path):
    """Convert YAML file to JSON file."""
    try:
        with open(yaml_path, 'r') as yf:
            data = yaml.safe_load(yf)

        with open(json_path, 'w') as jf:
            json.dump(data, jf, indent=4)

        print(f"✅ Converted '{yaml_path}' → '{json_path}'")
    except FileNotFoundError:
        print(f"❌ YAML file not found: {yaml_path}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ YAML parsing error: {e}", file=sys.stderr)
        sys.exit(1)

def send_payload(url, json_path):
    """Send JSON payload to API via POST."""
    try:
        with open(json_path, 'r') as jf:
            payload = json.load(jf)

        print(f"🚀 Sending payload from '{json_path}' to '{url}'...")
        response = requests.post(url, json=payload, verify=False, timeout=15)

        print(f"➡️ Status: {response.status_code}")
        if response.ok:
            print("✅ Success!")
        else:
            print("❌ Failed!")
        print("Response Body:")
        print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    convert_yaml_to_json(YAML_FILE, JSON_FILE)
    send_payload(API_URL, JSON_FILE)

if __name__ == "__main__":
    main()
