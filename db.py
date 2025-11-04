import os
import json

if os.path.exists("users.json"):
    with open("users.json") as f:
        users = json.load(f)
else:
    users = {}


def add_user(user_id, credential_id, public_key, sign_count):
    users[user_id] = {
        "credential_id": credential_id,
        "public_key": public_key,
        "sign_count": sign_count,
    }
    _commit()


def get_user_by_id(user_id):
    return users[user_id]


def set_user_sign_count(user_id, sign_count):
    users[user_id]["sign_count"] = sign_count
    _commit()


def _commit():
    with open("users.json", "w") as f:
        f.write(json.dumps(users))
