# firebase function libraries
from firebase_functions import https_fn
from firebase_admin import initialize_app, credentials

# genai libraries
from google import genai

# The Firebase Admin SDK to access Cloud Firestore.
from firebase_admin import initialize_app, firestore

# general imports
from flask import jsonify
from datetime import datetime

creds = credentials.Certificate("./service-account.json")
initialize_app(creds)
fsdb = firestore.client()
genai_client = genai.Client(api_key="AIzaSyDTmJn0kWr5ukWkxeWgMHZn_GY4il4xl1U")

def get_completions(prompt: str) -> str:
    response = genai_client.models.generate_content(
        model="gemini-1.5-flash-001",
        contents=prompt,
    )
    return response

def _get_transactions():
    docs = fsdb.collection("transactions").stream()

    dicts = []
    for doc in docs:
        record = {}
        result = doc.to_dict()
        for key in result:
            if isinstance(result[key], firestore.GeoPoint):
                record[key] = str(result[key].latitude)+','+str(result[key].longitude)
                continue
            record[key] = result[key]
        record["id"] = doc.id
        dicts.append(record)

    return dicts

@https_fn.on_request()
def get_transactions(req: https_fn.Request) -> https_fn.Response:
    return jsonify(_get_transactions())

@https_fn.on_request()
def add_transaction(req: https_fn.Request) -> https_fn.Response:
    data = req.get_json()
    # i.e March 22, 2025 at 8:15:00 AM UTC-4
    date_format = "%B %d, %Y at %I:%M:%S %p UTC%z"
    record = {
        "datetime": firestore.TimeStamp.FromDateTime(datetime.strptime(data["datetime"], date_format)),
        "location": firestore.GeoPoint(data["location"][0], data["location"][1]),
        "merchant": data["merchant"],
        "status": data["status"],
        "products": data["products"]
    }
    doc_ref = fsdb.collection("transactions").add(record)
    return https_fn.Response(f"Added {doc_ref.id} to transactions") 