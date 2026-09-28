import json
import time

with open("../API/transactions.json") as f:
    transactions = json.load(f)

lookup = {t["id"]: t for t in transactions}


def linear_search(transactions, target_id):
    for t in transactions:
        if t["id"] == target_id:
            return t
    return None


def dict_lookup(d, target_id):
    return d.get(target_id)


def measure(func, arg, target_id, repeats=1000):
    start = time.perf_counter()
    for _ in range(repeats):
        func(arg, target_id)
    return time.perf_counter() - start


cases = {
    "first record (id 1)": 1,
    "last record (id 1000)": 1000,
    "missing id (99999)": 99999,
}

print(f"{'Case':<25}{'Linear (s)':<15}{'Dict (s)':<15}")
for name, target in cases.items():
    t_linear = measure(linear_search, transactions, target)
    t_dict = measure(dict_lookup, lookup, target)
    print(f"{name:<25}{t_linear:<15.6f}{t_dict:<15.6f}")