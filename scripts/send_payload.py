import requests
import json

# The API endpoint
url = ""

# Open and read the json data from 
with open('data.json', 'r') as file:
    data = json.load("")

# A POST request to the API
response = requests.post(url, json=data)

# Print the response
print(response.json())
