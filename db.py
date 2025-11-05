import os
import json

if os.path.exists("users.json"):
    with open("users.json") as f:
        users = json.load(f)
else:
    users = {}


def add_user(user_id, data):
    users[user_id] = data
    _commit()


def get_user_by_id(user_id):
    return users[user_id]


def update_user(user_id, data):
    users[user_id].update(data)
    _commit()


def _commit():
    with open("users.json", "w") as f:
        f.write(json.dumps(users))
