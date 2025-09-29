import requests
import json
import yaml
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

    with open(json_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    with open(json_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

    logging.info(f"✅ Converted '{yaml_file_path}' to '{json_file_path}'")

# Function to send JSON payload to API
def send_payload(url, json_payload_path):
    """Sends a JSON payload from a file to a URL via POST request."""
    with open(json_payload_path, 'r') as file:
        data = json.load(file)
    logging.info(f"✅ Converted '{yaml_file_path}' to '{json_file_path}'")

# Function to send JSON payload to API
def send_payload(url, json_payload_path):
    """Sends a JSON payload from a file to a URL via POST request."""
    with open(json_payload_path, 'r') as file:
        data = json.load(file)

    headers = {'Content-Type': 'application/json'}
    logging.info(f"🚀 Sending payload from '{json_payload_path}' to '{url}'...")
    try:
        response = requests.post(url, json=data, headers=headers, verify=False)
        logging.info(f"➡️ Response Status Code: {response.status_code}")
    headers = {'Content-Type': 'application/json'}
    logging.info(f"🚀 Sending payload from '{json_payload_path}' to '{url}'...")
    try:
        response = requests.post(url, json=data, headers=headers, verify=False)
        logging.info(f"➡️ Response Status Code: {response.status_code}")
        if response.ok:
            logging.info("✅ Request was successful.")
            logging.info(f"Response Body:\n{response.text}")
            logging.info("✅ Request was successful.")
            logging.info(f"Response Body:\n{response.text}")
        else:
            logging.error("❌ Request failed.")
            logging.error(f"Response Body:\n{response.text}")
            logging.error("❌ Request failed.")
            logging.error(f"Response Body:\n{response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Network error - {e}")
        logging.error(f"❌ Network error - {e}")

# Main function
# Main function
def main():
    api_url = "https://sapient-duality-469110-d9.el.r.appspot.com/data"

    # Option 1: Use Git to detect changes
    # changed_yaml_files = get_changed_yaml_files()

    # Option 2: Hardcoded file list
    changed_yaml_files = ["/home/g2021wb86154/Declaration-files/google-cloud/central-india/kafka/dev-iot.yaml"]

    if not changed_yaml_files:
        logging.info("✅ No new or modified YAML files found.")
        return

    for yaml_file in changed_yaml_files:
        if not os.path.exists(yaml_file):
            logging.error(f"❌ File does not exist: {yaml_file}")
            continue

        json_file = os.path.splitext(os.path.basename(yaml_file))[0] + '.json'
        try:
            convert_yaml_to_json(yaml_file, json_file)
            send_payload(api_url, json_file)
        except Exception as e:
            logging.error(f"❌ Unexpected error: {e}")
    api_url = "https://sapient-duality-469110-d9.el.r.appspot.com/data"

    # Option 1: Use Git to detect changes
    # changed_yaml_files = get_changed_yaml_files()

    # Option 2: Hardcoded file list
    changed_yaml_files = ["/home/g2021wb86154/Declaration-files/google-cloud/central-india/kafka/dev-iot.yaml"]

    if not changed_yaml_files:
        logging.info("✅ No new or modified YAML files found.")
        return

    for yaml_file in changed_yaml_files:
        if not os.path.exists(yaml_file):
            logging.error(f"❌ File does not exist: {yaml_file}")
            continue

        json_file = os.path.splitext(os.path.basename(yaml_file))[0] + '.json'
        try:
            convert_yaml_to_json(yaml_file, json_file)
            send_payload(api_url, json_file)
        except Exception as e:
            logging.error(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()