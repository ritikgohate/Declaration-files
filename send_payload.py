import requests
import json
import yaml
import sys
import subprocess
import os

# Function to detect new or modified YAML files using Git
def get_changed_yaml_files(base_branch='dev'):
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
        print(f"❌ Git command failed: {e}", file=sys.stderr)
        return []

# rebase the dev to master
def rebase_dev_to_master():
    try:
        subprocess.run(['git', 'fetch', 'origin'], check=True)
        subprocess.run(['git', 'rebase', 'origin/master'], check=True)
        print("✅ Rebased dev to master successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Rebase failed: {e}", file=sys.stderr)
        return


# Function to convert YAML to JSON
def convert_yaml_to_json(yaml_file_path, json_file_path):
    """Converts a YAML file to a JSON file."""
    with open(yaml_file_path, 'r') as yaml_file:
        data = yaml.safe_load(yaml_file)

    with open(json_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

    print(f"✅ Converted '{yaml_file_path}' to '{json_file_path}'")

# Function to send JSON payload to API
def send_payload(url, json_payload_path):
    """Sends a JSON payload from a file to a URL via POST request."""
    with open(json_payload_path, 'r') as file:
        data = json.load(file)

    print(f"🚀 Sending payload from '{json_payload_path}' to '{url}'...")
    response = requests.post(url, json=data, verify=False)

    print(f"➡️ Response Status Code: {response.status_code}")
    if response.ok:
        print("✅ Request was successful.")
        print("Response Body:")
        print(response.text)
    else:
        print("❌ Request failed.")
        print("Response Body:")
        print(response.text)

# Main function
def main():
    api_url = "https://sapient-duality-469110-d9.el.r.appspot.com/data"
    changed_yaml_files = get_changed_yaml_files()

    if not changed_yaml_files:
        print("✅ No new or modified YAML files found.")
        return

    if changed_yaml_files:
        rebase_dev_to_master()
        return

    for yaml_file in changed_yaml_files:
        json_file = os.path.splitext(os.path.basename(yaml_file))[0] + '.json'
        try:
            convert_yaml_to_json(yaml_file, json_file)
            send_payload(api_url, json_file)
        except FileNotFoundError as e:
            print(f"❌ Error: File not found - {e}", file=sys.stderr)
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error - {e}", file=sys.stderr)
        except Exception as e:
            print(f"❌ Unexpected error: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
 