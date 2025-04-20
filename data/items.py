
import json
import os

with open(os.path.join(os.path.dirname(__file__), "items.json")) as f:
    data = json.load(f)

ITEM_TYPE_MAP = {
    item["name"]: item["type"]
    for pool in data.values()
    for item in pool
}

ITEM_ELEMENT_MAP = {
    "pyrith": "pyrith",
    "Blazing Sword": "pyrith",
    "Fireproof Helm": "pyrith",
    "aquarem": "aquarem",
    "Hydro Cutter": "aquarem",
    "Hydro Cloak": "aquarem",
    "terravite": "terravite",
    "Terra Hammer": "terravite",
    "Golem Plate": "terravite",
    "aythest": "aythest",
    "Storm Dagger": "aythest",
    "Skyguard Boots": "aythest",
    "voidite": "voidite",
    "Void Saber": "voidite",
    "Void Robe": "voidite",
}