import os
import time
import json

CACHE_DIR = "_CACHE_ROBLOX_OS_"
CACHE_DURATION = 6 * 60 * 60

os.makedirs(CACHE_DIR, exist_ok=True)

def sanitize_filename(name):
    return "".join(c for c in name if c.isalnum() or c in "_-")

def read_cache(username):
    f = os.path.join(CACHE_DIR, f"{sanitize_filename(username)}.json")
    if not os.path.exists(f):
        return None
    with open(f, "r", encoding="utf8") as fp:
        data = json.load(fp)
    if time.time() - data["timestamp"] < CACHE_DURATION:
        return data["info"]
    return None

def write_cache(username, info):
    f = os.path.join(CACHE_DIR, f"{sanitize_filename(username)}.json")
    with open(f, "w", encoding="utf8") as fp:
        json.dump({"timestamp": time.time(), "info": info}, fp, indent=4)
