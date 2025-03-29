import json
from datetime import datetime

from firebase_admin import initialize_app, credentials, firestore

creds = credentials.Certificate("./service-account.json")
app = initialize_app(creds)
fsdb = firestore.client(app)

path = "./doordash.txt"
with open(path, "r") as file:
    data = json.load(file)

for transaction in data['transactions']:
    fs_transaction = {
        "merchant": "DoorDash",
        "datetime": datetime.strptime(transaction["datetime"], "%Y-%m-%dT%H:%M:%S%z"),
        "status": transaction["order_status"],
        "products": [
            {
                "id": product["external_id"],
                "name": product["name"],
                "price": product["price"]["total"]
            } for product in transaction["products"]
        ]
    }
    key = transaction["id"]
    fsdb.collection("transactions").document(str(key)).set(fs_transaction)