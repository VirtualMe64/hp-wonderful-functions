from functions.main import find_cheaper_store, give_recommendation

test_transaction = {
    "merchant": "Doordash: morton's steakhouse",
    "location": [37.774929, -122.419418],
    "products": ["ribeye steak"]
}

recommendation = give_recommendation(test_transaction)
print(recommendation)