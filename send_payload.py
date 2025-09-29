import requests
import json
import yaml
import sys
import subprocess
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Function to detect new or modified YAML files using Git
def get_changed_yaml_files(base_branch='payload'):
    """Detects new and modified YAML files compared to the base branch."""
    try:
        subprocess.run(['git', 'fetch'], check=True)
        result = subprocess.run(
            ['git', 'diff', '--name-status', f'origin/{base_branch}...HEAD'],
            stdout=subprocess.PIPE,
            text=True,
            check=True
        )
        changed_files = result.stdout.strip().split('\n')
        yaml_changes = []

        for line in changed_files:
            if not line.strip():
                continue
            status, file_path = line.split('\t')
            if file_path.endswith(('.yaml', '.yml')) and status in ['A', 'M']:
                yaml_changes.append(file_path)

        return yaml_changes

    except subprocess.CalledProcessError as e:
        logging.error(f"Git command failed: {e}")
        return []

# Function to convert YAML to JSON
def convert_yaml_to_json(yaml_file_path, json_file_path):
    """Converts a YAML file to a JSON file."""
    with open(yaml_file_path, 'r') as yaml_file:
        data = yaml.safe_load(yaml_file)

    with open(json_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

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
        if response.ok:
            logging.info("✅ Request was successful.")
            logging.info(f"Response Body:\n{response.text}")
        else:
            logging.error("❌ Request failed.")
            logging.error(f"Response Body:\n{response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Network error - {e}")

# Main function
def main():
    api_url = "https://sapient-duality-469110-d9.el.r.appspot.com/data"

    # Option 1: Use Git to detect changes
    # changed_yaml_files = get_changed_yaml_files()

    # Option 2: Hardcoded file list
    changed_yaml_files = ["./google-cloud/central-india/kafka/dev-iot.yaml"]

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