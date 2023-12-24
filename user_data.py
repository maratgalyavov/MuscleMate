import json
import os
from config import USER_DATA_FILE

def load_user_data(user_id):
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            data = json.load(f)
            return data.get(str(user_id), {})
    return {}


def save_user_data(user_id, data):
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            all_data = json.load(f)
    else:
        all_data = {}
    all_data[str(user_id)] = data
    with open(USER_DATA_FILE, "w") as f:
        json.dump(all_data, f)
