import json
import os
from config import USER_DATA_FILE

def load_user_data(user_id):
    """
    Loads user-specific data from a file, returning the data for the given user ID.
    """
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            data = json.load(f)
            return data.get(str(user_id), {})
    return {}


def save_user_data(user_id, data):
    """
    Saves user-specific data to a file, updating or adding the data for the given user ID.
    """
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            all_data = json.load(f)
    else:
        all_data = {}
    all_data[str(user_id)] = data
    with open(USER_DATA_FILE, "w") as f:
        json.dump(all_data, f)
