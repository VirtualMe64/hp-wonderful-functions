from firebase_admin import initialize_app, credentials, firestore
from google.cloud.firestore import GeoPoint
from datetime import datetime
import os

EMULATED = False

if EMULATED:
  oldFS = os.environ['FIRESTORE_EMULATOR_HOST'] if 'FIRESTORE_EMULATOR_HOST' in os.environ else None
  os.environ['FIRESTORE_EMULATOR_HOST'] = '127.0.0.1:8080'

creds = credentials.Certificate("./service-account.json")
app = initialize_app(creds)
fsdb = firestore.client(app)

mockTransactions = [
    {
      "id": 1,
      "datetime": '2025-03-22T08:15:00Z',
      "location": [47.6061, 122.3328],
      "merchant": "Starbucks",
      "status": "COMPLETED",
      "products": [{ "id": 101, "name": "Latte", "price": 4.50 }]
    },
    {
      "id": 2,
      "datetime": '2025-03-23T10:30:00Z',
      "location": [47.6061, 122.3328],
      "merchant": "Dunkin'",
      "status": "COMPLETED",
      "products": [{ "id": 102, "name": "Cold Brew", "price": 3.75 }]
    },
    {
      "id": 3,
      "datetime": '2025-03-24T07:45:00Z',
      "location": [47.6061, 122.3328],
      "merchant": "Blue Bottle Coffee",
      "status": "PENDING",
      "products": [{ "id": 103, "name": "Cappuccino", "price": 5.00 }]
    },
    {
      "id": 4,
      "datetime": '2025-03-25T09:00:00Z',
      "location": [47.6061, 122.3328],
      "merchant": "Starbucks",
      "status": "COMPLETED",
      "products": [{ "id": 104, "name": "Espresso", "price": 3.00 }]
    },
    {
      "id": 5,
      "datetime": '2025-03-26T11:15:00Z',
      "location": [47.6061, 122.3328],
      "merchant": "Peet's Coffee",
      "status": "FAILED",
      "products": [{ "id": 105, "name": "Americano", "price": 3.25 }]
    },
    {
      "id": 6,
      "datetime": '2025-03-22T13:45:00Z',
      "location": [47.6061, 122.3328],
      "merchant": "Whole Foods",
      "status": "COMPLETED",
      "products": [
        { "id": 106, "name": "Organic Bananas", "price": 2.99 },
        { "id": 107, "name": "Almond Milk", "price": 3.49 }
      ]
    },
    {
      "id": 7,
      "datetime": '2025-03-23T16:20:00Z',
      "location": [47.6061, 122.3328],
      "merchant": "Amazon",
      "status": "COMPLETED",
      "products": [{ "id": 108, "name": "Wireless Mouse", "price": 25.99 }]
    },
    {
      "id": 8,
      "datetime": '2025-03-24T18:05:00Z',
      "location": [47.6061, 122.3328],
      "merchant": "Target",
      "status": "PENDING",
      "products": [
        { "id": 109, "name": "Shampoo", "price": 6.99 },
        { "id": 110, "name": "Conditioner", "price": 6.99 }
      ]
    },
    {
      "id": 9,
      "datetime": '2025-03-25T19:30:00Z',
      "location": [47.6061, 122.3328],
      "merchant": "Best Buy",
      "status": "COMPLETED",
      "products": [{ "id": 111, "name": "USB-C Charger", "price": 19.99 }]
    },
    {
      "id": 10,
      "datetime": '2025-03-26T20:45:00Z',
      "location": [47.6061, 122.3328],
      "merchant": "Walmart",
      "status": "FAILED",
      "products": [{ "id": 112, "name": "Desk Lamp", "price": 15.49 }]
    }
]

for transaction in mockTransactions:
    transaction["datetime"] = datetime.strptime(transaction["datetime"], '%Y-%m-%dT%H:%M:%SZ')
    transaction["location"] = GeoPoint(transaction["location"][0], transaction["location"][1])

    key = transaction.pop("id")
    fsdb.collection("transactions").document(str(key)).set(transaction)

if EMULATED:
  if oldFS is None:
      del os.environ['FIRESTORE_EMULATOR_HOST']
  else:
      os.environ['FIRESTORE_EMULATOR_HOST'] = oldFS
