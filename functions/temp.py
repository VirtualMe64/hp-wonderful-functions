import requests

url = "http://127.0.0.1:5001/hp-wonderful/us-central1/get_chat"
data = {"message": "How do I make a million dollars today?"}

response = requests.post(url, json=data)

if response.status_code == 200:
    print(response.text)  # Print the response if successful
else:
    print(f"Error {response.status_code}: {response.text}")  # Print error message