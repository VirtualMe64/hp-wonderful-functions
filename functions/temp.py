import requests

url = "https://us-central1-hp-wonderful.cloudfunctions.net/get_chat"
data = {"message": "What stock should I buy?"}

response = requests.post(url, json=data)

if response.status_code == 200:
    print(response.text)  # Print the response if successful
else:
    print(f"Error {response.status_code}: {response.text}")  # Print error message