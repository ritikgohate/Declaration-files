import yaml
import json

# Function to convert YAML file to JSON payload format
def convert_yaml_to_payload(yaml_file_path, payload_file_path):
    try:
        # Step 1: Load YAML file
        with open(yaml_file_path, 'r') as yaml_file:
            data = yaml.safe_load(yaml_file)

        # Step 2: Convert to JSON string (pretty format)
        json_payload = json.dumps(data, indent=4)

        # Step 3: Save to payload file
        with open(payload_file_path, 'w') as payload_file:
            payload_file.write(json_payload)

        print(f"Payload saved to '{payload_file_path}'")

    except Exception as e:
        print(f"Error: {e}")

# Example usage
yaml_input = 'dev-iot.yaml'               # Input YAML file
payload_output = 'dev-iot-payload.json'   # Output payload file

convert_yaml_to_payload(yaml_input, payload_output)
