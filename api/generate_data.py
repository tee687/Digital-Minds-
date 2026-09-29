import json, random

records = []
for i in range(1, 1001):
    records.append({
        "id": i,
        "type": random.choice(["received", "payment", "transfer", "deposit"]),
        "amount": random.randint(500, 50000),
        "sender": "Jane Smith",
        "receiver": "Samuel Carter",
        "timestamp": "2024-05-10 16:30:51"
    })

with open("transactions.json", "w") as f:
    json.dump(records, f, indent=2)