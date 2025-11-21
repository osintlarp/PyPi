from bs4 import BeautifulSoup
import time
import json
from datetime import datetime, timezone
import os

from .utils import try_request, get_user_agent
from .cache import read_cache, write_cache
from .cprint import info, error, success

USER_PRESENCE_MAP = {
    0: "Offline",
    1: "Online",
    2: "In-Game",
    3: "In-Studio",
    4: "Invisible"
}

ROBLOX_BADGE_TABLE = {
    1: "Administrator",
    2: "Friendship",
    3: "Combat Initiation",
    4: "Warrior",
    5: "Bloxxer",
    6: "Homestead",
    7: "Bricksmith",
    8: "Inviter",
    12: "Veteran",
    14: "Ambassador",
    17: "Official Model Maker",
    18: "Welcome To The Club"
}

def search_by_username(username):
    info(f"Searching Roblox UID for {username}")
    url = f"https://users.roblox.com/v1/users/search?keyword={username}&limit=10"
    headers = {"User-Agent": get_user_agent()}
    r, err = try_request("get", url, headers=headers)
    if r and r.status_code == 200:
        data = r.json().get("data", [])
        for u in data:
            if u.get("name", "").lower() == username.lower():
                uid = str(u["id"])
                success(f"Found UID {uid} for user {username}")
                return uid
    error(f"User {username} not found")
    return None

def get_previous_usernames(uid):
    info(f"Fetching previous usernames for {uid}")
    url = f"https://users.roblox.com/v1/users/{uid}/username-history?limit=50"
    headers = {"User-Agent": get_user_agent()}
    r, _ = try_request("get", url, headers=headers)
    if r and r.status_code == 200:
        return [x["name"] for x in r.json().get("data", [])]
    return []

def get_groups(uid):
    info(f"Fetching groups for {uid}")
    url = f"https://groups.roblox.com/v2/users/{uid}/groups/roles"
    headers = {"User-Agent": get_user_agent()}
    r, _ = try_request("get", url, headers=headers)
    if r and r.status_code == 200:
        result = []
        for g in r.json().get("data", []):
            grp = g["group"]
            result.append({
                "name": grp.get("name"),
                "link": f"https://www.roblox.com/groups/{grp.get('id')}",
                "members": grp.get("memberCount")
            })
        return result
    return []

def get_about_me(uid):
    info(f"Fetching profile description for {uid}")
    url = f"https://www.roblox.com/users/{uid}/profile"
    headers = {"User-Agent": get_user_agent()}
    r, _ = try_request("get", url, headers=headers)
    if r and r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        span = soup.find("span", class_="profile-about-content-text")
        if span:
            return span.text.strip()
    return "Not available"

def get_entity_list(uid, entity_type):
    info(f"Fetching {entity_type} list for {uid}")
    results = []
    cursor = ""
    while True:
        url = f"https://friends.roblox.com/v1/users/{uid}/{entity_type}?limit=100&cursor={cursor}"
        headers = {"User-Agent": get_user_agent()}
        r, _ = try_request("get", url, headers=headers)
        if not r or r.status_code != 200:
            break
        for item in r.json().get("data", []):
            name = item.get("displayName") or item.get("name")
            user_id = item.get("id")
            if name and user_id:
                results.append({
                    "name": name,
                    "url": f"https://www.roblox.com/users/{user_id}/profile"
                })
        cursor = r.json().get("nextPageCursor")
        if not cursor:
            break
        time.sleep(0.2)
    return results

def get_presence(uid):
    info(f"Fetching presence for {uid}")
    url = "https://presence.roblox.com/v1/presence/users"
    headers = {"User-Agent": get_user_agent()}
    payload = {"userIds": [int(uid)]}
    r, _ = try_request("post", url, headers=headers, json_payload=payload)
    if r and r.status_code == 200:
        return r.json()["userPresences"][0]
    return None

def get_badges(uid):
    info(f"Fetching badges for {uid}")
    url = f"https://accountinformation.roblox.com/v1/users/{uid}/roblox-badges"
    headers = {"User-Agent": get_user_agent()}
    r, _ = try_request("get", url, headers=headers)
    if r and r.status_code == 200:
        ids = [b["id"] for b in r.json()]
        return [ROBLOX_BADGE_TABLE[i] for i in ids if i in ROBLOX_BADGE_TABLE]
    return []

def get_promo_channels(uid):
    info(f"Fetching promo channels for {uid}")
    url = f"https://users.roblox.com/v1/users/{uid}/promotion-channels"
    headers = {"User-Agent": get_user_agent()}
    r, _ = try_request("get", url, headers=headers)
    if r and r.status_code == 200:
        return r.json().get("promotionChannels", {})
    return {}

def get_user_info(identifier, use_cache=True, **options):
    info(f"Starting Roblox lookup: {identifier}")
    cached = read_cache(identifier)
    if cached:
        return cached
    if identifier.isdigit():
        uid = identifier
    else:
        uid = search_by_username(identifier)
    if uid is None:
        return {"error": "User not found"}
    headers = {"User-Agent": get_user_agent()}
    url = f"https://users.roblox.com/v1/users/{uid}"
    r, err = try_request("get", url, headers=headers)
    if err or not r or r.status_code != 200:
        error(f"Failed to fetch user data for {uid}")
        return {"error": "Failed to fetch profile"}
    base = r.json()
    data = {
        "user_id": uid,
        "alias": base.get("name"),
        "display_name": base.get("displayName"),
        "description": base.get("description", ""),
        "is_banned": base.get("isBanned", False),
        "has_verified_badge": base.get("hasVerifiedBadge", False),
        "join_date": base.get("created")
    }
    try:
        dt = datetime.fromisoformat(base["created"].replace("Z", "+00:00"))
        d = datetime.now(timezone.utc) - dt
        y = d.days // 365
        ds = d.days % 365
        data["account_age"] = f"{y} Years, {ds} Days"
    except:
        data["account_age"] = "Unknown"
    def count(url):
        r, _ = try_request("get", url, headers=headers)
        if r and r.status_code == 200:
            return r.json().get("count", 0)
        return 0
    data["friends"] = count(f"https://friends.roblox.com/v1/users/{uid}/friends/count")
    data["followers"] = count(f"https://friends.roblox.com/v1/users/{uid}/followers/count")
    data["following"] = count(f"https://friends.roblox.com/v1/users/{uid}/followings/count")
    data["previous_usernames"] = get_previous_usernames(uid)
    data["groups"] = get_groups(uid)
    data["about_me"] = get_about_me(uid)
    data["friends_list"] = get_entity_list(uid, "friends")
    data["followers_list"] = get_entity_list(uid, "followers")
    data["following_list"] = get_entity_list(uid, "followings")
    presence = get_presence(uid)
    if presence:
        data["presence_status"] = USER_PRESENCE_MAP.get(presence["userPresenceType"])
        data["last_location"] = presence.get("lastLocation")
        data["current_place_id"] = presence.get("placeId")
        data["last_online_timestamp"] = presence.get("lastOnline")
    else:
        data["presence_status"] = "Unknown"
    data["roblox_badges"] = get_badges(uid)
    data["promotion_channels"] = get_promo_channels(uid)
    write_cache(identifier, data)
    success(f"Finished scraping {identifier}")
    return data
