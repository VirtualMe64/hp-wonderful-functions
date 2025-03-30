from main import find_cheaper_store, give_recommendation, kevinify_recommendation

test_transaction = {
    "merchant": "Doordash: morton's steakhouse",
    "location": [37.774929, -122.419418],
    "products": [{"name": "ribeye steak"}]
}

recommendation = give_recommendation(test_transaction)
print(recommendation)
kevinified_recommendation = kevinify_recommendation(recommendation["recommendation"])
recommendation["recommendation"] = kevinified_recommendation
print(recommendation)