import requests
import json

# The API endpoint
url = "http://10.88.0.4:8080/data"

# Open and read the JSON data
with open('/home/g2021wb86154/dev-iot.json', 'r') as file:
    data = json.load(file)  # ✅ Corrected: pass the file object, not an empty string

# A POST request to the API
response = requests.post(url, json=data, verify=False)  # ⚠️ Added verify=False to skip SSL verification (use with caution)

# Print the response
print(response.status_code)
print(response.text)
