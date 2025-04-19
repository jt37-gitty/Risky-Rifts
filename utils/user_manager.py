import os
import json

# File path setup
data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
users_file = os.path.join(data_dir, 'users.json')

_users = {}

def load():
    global _users
    os.makedirs(data_dir, exist_ok=True)
    if not os.path.exists(users_file):
        _users = {}
    else:
        with open(users_file, 'r') as f:
            _users = json.load(f)
    return _users

def save():
    with open(users_file, 'w') as f:
        json.dump(_users, f, indent=2)

def get():
    return _users
