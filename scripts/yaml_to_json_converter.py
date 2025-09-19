
import yaml
import json

# Function to convert YAML to JSON
def convert_yaml_to_json(yaml_file_path, json_file_path):
    try:
        # Load YAML file
        with open(yaml_file_path, 'r') as yaml_file:
            data = yaml.safe_load(yaml_file)

        # Write to JSON file
        with open(json_file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)

        print(f"✅ Successfully converted '{{yaml_file_path}}' to '{{json_file_path}}'")

    except Exception as e:
        print(f"❌ Error: {e}")

# Example usage
yaml_file = '/home/g2021wb86154/Declaration-files/google-cloud/central-india/kafka/dev-iot.yaml'      # Input YAML file name
json_file = 'dev-iot.json'      # Output JSON file name

convert_yaml_to_json(yaml_file, json_file)
