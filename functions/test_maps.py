from main import give_recommendation, kevinify_recommendation, send_text

test_transaction = {
    "merchant": "Instacart: morton's steakhouse",
    "location": [37.774929, -122.419418],
    "products": [{"name": "ribeye steak"}]
}

recommendation = give_recommendation(test_transaction)
print(recommendation)
kevinified_recommendation = kevinify_recommendation(recommendation["recommendation"], test_transaction)
recommendation["recommendation"] = kevinified_recommendation
print(recommendation)

send_text("Kevin is very upset about your spending habits!")