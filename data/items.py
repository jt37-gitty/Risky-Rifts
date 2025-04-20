
import json
import os

with open(os.path.join(os.path.dirname(__file__), "items.json")) as f:
    data = json.load(f)

ITEM_TYPE_MAP = {
    item["name"]: item["type"]
    for pool in data.values()
    for item in pool
}
