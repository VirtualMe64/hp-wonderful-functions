# firebase function libraries
from firebase_functions import https_fn
from firebase_admin import initialize_app, credentials, firestore

# genai libraries
from google import genai

# general imports
from flask import jsonify
from prompts import get_critique_prompt

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
def get_critique(req: https_fn.Request) -> https_fn.Response:
    prompt = get_critique_prompt(_get_transactions())
    response = get_completions(prompt)
    return response.text

@https_fn.on_request()
def get_transactions(req: https_fn.Request) -> https_fn.Response:
    return jsonify(_get_transactions())