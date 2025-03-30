# firebase function libraries
from firebase_functions import https_fn, firestore_fn
from firebase_admin import initialize_app, credentials, firestore

# genai libraries
from google import genai

# general imports
from flask import jsonify
from prompts import get_critique_prompt

import requests

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

@https_fn.on_request()
def get_transactions(req: https_fn.Request) -> https_fn.Response:
    return jsonify(_get_transactions())

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


# each time a new transaction is added to the "transactions" collection, give a recommendation
@firestore_fn.on_document_created(document="transactions/{transaction_id}")
def give_recommendation_on_transaction_creation(event: firestore_fn.Event) -> https_fn.Response:
    transaction_id = event.params["transaction_id"]
    doc = event.data.to_dict()
    transaction = fsdb.collection("transactions").document(transaction_id).get().to_dict()
    
    recommendation = give_recommendation(transaction)
    doc_ref = fsdb.collection("transactions").document(transaction_id)
    doc_ref.update({"recommendation": recommendation})


def give_recommendation(transaction: dict) -> dict:
    # first check if the item can be easily made at home
    
    # see if the merchant is doordash
    if "doordash" in transaction["merchant"].lower():
        result = find_cheaper_store(transaction)
        
        # write a recommendation based on the result
        prompt = f"Write a short message describing the recommendation to go to this close restaurant rather than ordering from doordash {result}"
        response = get_completions(prompt)
        recommendation = response.text
        return {"recommendation": recommendation, "address": get_address(geo_to_coords(result["geometry"]["location"]))}
    
    # determine if the merchant is a chain or not
    prompt = f"Is the merchant {transaction['merchant']} a chain? (respond with only yes or no)"
    response = get_completions(prompt)
    is_chain = response.text
    if "yes" in is_chain.lower():
        # check if item is store brand or not
        prompt = f"Is the product {product_at_home} a store brand? (respond with only yes or no)"
        response = get_completions(prompt)
        is_store_brand = response.text
        
        # find a cheaper store
        result = find_cheaper_store(transaction)
        
        # write a recommendation based on the result
        prompt = f"Write a short message describing the recommendation to buy the product at this cheaper store {result}"
        if not is_store_brand:
            prompt += f" or to find a cheaper store brand product"
        response = get_completions(prompt)
        recommendation = response.text
        return {"recommendation": recommendation, "address": get_address(geo_to_coords(result["geometry"]["location"]))}
    
    product_at_home = None
    for product in transaction["products"]:
        prompt = f"Can the product {product} be easily made at home? (respond with only yes or no)"
        response = get_completions(prompt)
        if "yes" in response.text.lower():
            product_at_home = product
            break
        
    if product_at_home:
        # list key items that would be needed to buy to make this product
        prompt = f"What are the key items that would be needed to buy to make the product {product_at_home}? (respond with a comma separated list of words)"
        response = get_completions(prompt)
        items_needed = response.text
        print(items_needed)
        # find a location that sells the items needed using maps api
        location = transaction["location"]
        result = query_maps(items_needed, location)
        
        # return the result
        # write a recommendation based on the result
        prompt = f"Write a short message describing the recommendation for them to make the product at home by buying the items at the following location instead of buying the completed product {result}"
        response = get_completions(prompt)
        recommendation = response.text
        return {"recommendation": recommendation, "address": get_address(geo_to_coords(result["geometry"]["location"]))}
    
    # determine if the 
    return {"recommendation": ""}



def geo_to_coords(geo: str) -> tuple:
    return [geo["lat"], geo["lng"]]
    
def query_maps(items_needed: str, location: tuple) -> str:
    # get merchant category
    prompt = f"What kind of store sells the items {items_needed}? respond with a couple comma separated words"
    response = get_completions(prompt)
    merchant_category = response.text
    print(merchant_category)
    maps_api_key = "AIzaSyAD2DJZyMFGL9yWbYPSZWOqKVDzHVruh4M"
    maps_endpoint = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?" + \
        f"location={location[0]},{location[1]}" + \
        f"&radius=400" + \
        f"&keyword={merchant_category}" + \
        f"&key={maps_api_key}"
    maps_endpoint = maps_endpoint.replace(" ", "")
    
    # get response from maps api
    response = requests.get(maps_endpoint)
    responseJson = response.json()
    results = responseJson["results"]
    
    # return first result
    return results[0]
    
    
# on new transaction, analyze for cheaper options
def find_cheaper_store(transaction: dict) -> dict:
    # get name of merchant
    merchant = transaction["merchant"]
    location = transaction["location"] # lat, long
    
    # get merchant category e.g. "grocery", "restaurant", "shopping", "gas", ... using gemini
    prompt = f"What is the category of the merchant {merchant} in one word?"
    response = get_completions(prompt)
    merchant_category = response.text
    
    # get products
    products = transaction["products"]
    # get product categories
    prompt = f"What is the category of the product {products} in one word? make a comma separated list of words"
    response = get_completions(prompt)
    product_categories = response.text
    
    # use maps api to find stores in the area that sell the products
    maps_api_key = "AIzaSyAD2DJZyMFGL9yWbYPSZWOqKVDzHVruh4M"
    maps_endpoint = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?" + \
        f"location={location[0]},{location[1]}" + \
        f"&radius=400" + \
        f"&keyword={merchant_category},{product_categories}" + \
        f"&key={maps_api_key}"
    maps_endpoint = maps_endpoint.replace(" ", "")
    
    # get response from maps api
    response = requests.get(maps_endpoint)
    responseJson = response.json()
    results = responseJson["results"]
    
    # for each result location and product use doordash api to find the pickup pricing for each product
    locations = []
    for result in results:
        # get address of result from lat, long
        coords = result["geometry"]["location"]
        coords = [coords["lat"], coords["lng"]]
        
        # convert coords to address
        address = get_address(coords)
        
        locations.append(f"{result['name']} at {address} with rating {result['rating']} and {result['user_ratings_total']} reviews")
        
    # use llm to choose cheapest location, return just a number index
    prompt = f"Guess which option might be the cheapest, only return the index of the location the only output should be a number: {locations}"
    response = get_completions(prompt)
    cheapest_location = int(response.text)
    
    return results[cheapest_location]
        
        
def get_address(coords: dict) -> str:
    # use maps api to get address
    maps_api_key = "AIzaSyAD2DJZyMFGL9yWbYPSZWOqKVDzHVruh4M"
    maps_endpoint = f"https://maps.googleapis.com/maps/api/geocode/json?" + \
        f"latlng={coords[0]},{coords[1]}" + \
        f"&key={maps_api_key}"
    response = requests.get(maps_endpoint)
    responseJson = response.json()
    return responseJson["results"][0]["formatted_address"]
    
