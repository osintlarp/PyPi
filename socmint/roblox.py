from bs4 import BeautifulSoup
import time
import json
from datetime import datetime, timezone
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from .utils import try_request, get_user_agent
from .cache import read_cache, write_cache
from .cprint import info, error, success
from . import config

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

def run_multi(tasks):
    if not config.USE_MULTI:
        results = {}
        for name, func, args in tasks:
            try:
                results[name] = func(*args)
            except:
                results[name] = None
        return results
    results = {}
    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as exe:
        futures = {exe.submit(func, *args): name for name, func, args in tasks}
        for fut in as_completed(futures):
            key = futures[fut]
            try:
                results[key] = fut.result()
            except:
                results[key] = None
    return results

def get_csrf_token(cookie):
    try:
        r = requests.post(
            "https://auth.roblox.com/v2/login",
            cookies={".ROBLOSECURITY": cookie},
            json={},
            verify=config.VERIFY_SSL,
            timeout=config.TIMEOUT
        )
        token = r.headers.get("x-csrf-token")
        if not token:
            return None
        return token
    except:
        return None

def report_worker(url, headers, req_cookies, payload):
    try:
        r = requests.post(
            url,
            headers=headers,
            cookies=req_cookies,
            data=json.dumps(payload),
            verify=config.VERIFY_SSL,
            timeout=config.TIMEOUT
        )
        return r.status_code, (r.json() if r.status_code in [200, 201] else r.text)
    except Exception as e:
        return None, str(e)

def report_user(target_username, cookie, reporter_uid, total_reports=1):
    target_uid = search_by_username(target_username)
    if not target_uid:
        error("User not found")
        return
    csrf_token = get_csrf_token(cookie)
    if not csrf_token:
        error("Invalid CSRF")
        return

    url = "https://apis.roblox.com/abuse-reporting/v2/abuse-report"
    headers = {
        "content-type": "application/json;charset=utf-8",
        "accept": "application/json, text/plain, */*",
        "user-agent": get_user_agent(),
        "x-csrf-token": csrf_token
    }
    req_cookies = {
        ".ROBLOSECURITY": cookie,
        "GuestData": f"UserID={reporter_uid}"
    }
    payload = {
        "tags": {
            "ENTRY_POINT": {"valueList": [{"data": "website"}]},
            "REPORTED_ABUSE_CATEGORY": {"valueList": [{"data": "dating"}]},
            "REPORTED_ABUSE_VECTOR": {"valueList": [{"data": "user_profile"}]},
            "REPORTER_COMMENT": {"valueList": [{"data": ""}]},
            "SUBMITTER_USER_ID": {"valueList": [{"data": str(reporter_uid)}]},
            "REPORT_TARGET_USER_ID": {"valueList": [{"data": str(target_uid)}]}
        }
    }

    tasks = []
    for i in range(total_reports):
        tasks.append((str(i+1), report_worker, [url, headers, req_cookies, payload]))

    results = run_multi(tasks)

    for k, r in results.items():
        if not r:
            error(f"[{k}] Error")
        else:
            code, data = r
            if code in [200, 201]:
                success(f"[{k}] {data}")
            else:
                error(f"[{k}] {code} - {data}")

def search_by_username(username):
    url = f"https://users.roblox.com/v1/users/search?keyword={username}&limit=10"
    headers = {"User-Agent": get_user_agent()}
    r, _ = try_request("get", url, headers=headers)
    if r and r.status_code == 200:
        for u in r.json().get("data", []):
            if u.get("name", "").lower() == username.lower():
                return str(u["id"])
    return None

def get_previous_usernames(uid):
    url = f"https://users.roblox.com/v1/users/{uid}/username-history?limit=50"
    headers = {"User-Agent": get_user_agent()}
    r, _ = try_request("get", url, headers=headers)
    if r and r.status_code == 200:
        return [x["name"] for x in r.json().get("data", [])]
    return []

def get_groups(uid):
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
    url = f"https://www.roblox.com/users/{uid}/profile"
    headers = {"User-Agent": get_user_agent()}
    r, _ = try_request("get", url, headers=headers)
    if not r:
        return "Not available"
    soup = BeautifulSoup(r.text, "html.parser")
    span = soup.find("span", class_="profile-about-content-text")
    return span.text.strip() if span else "Not available"

def get_entity_list(uid, entity_type, limit=500):
    results = []
    cursor = ""
    while True:
        url = f"https://friends.roblox.com/v1/users/{uid}/{entity_type}?limit=100&cursor={cursor}"
        headers = {"User-Agent": get_user_agent()}
        r, _ = try_request("get", url, headers=headers)
        if not r or r.status_code != 200:
            break
        data = r.json().get("data", [])
        if not data:
            break
        for item in data:
            name = item.get("displayName") or item.get("name")
            user_id = item.get("id")
            if name and user_id:
                results.append({
                    "name": name,
                    "url": f"https://www.roblox.com/users/{user_id}/profile"
                })
            if len(results) >= limit:
                return results
        cursor = r.json().get("nextPageCursor")
        if not cursor:
            break
    return results

def get_presence(uid):
    url = "https://presence.roblox.com/v1/presence/users"
    headers = {"User-Agent": get_user_agent()}
    payload = {"userIds": [int(uid)]}
    r, _ = try_request("post", url, headers=headers, json_payload=payload)
    if r and r.status_code == 200:
        return r.json()["userPresences"][0]
    return None

def get_badges(uid):
    url = f"https://accountinformation.roblox.com/v1/users/{uid}/roblox-badges"
    headers = {"User-Agent": get_user_agent()}
    r, _ = try_request("get", url, headers=headers)
    if r and r.status_code == 200:
        return [ROBLOX_BADGE_TABLE.get(b["id"]) for b in r.json() if b["id"] in ROBLOX_BADGE_TABLE]
    return []

def get_promo_channels(uid):
    url = f"https://users.roblox.com/v1/users/{uid}/promotion-channels"
    headers = {"User-Agent": get_user_agent()}
    r, _ = try_request("get", url, headers=headers)
    if r and r.status_code == 200:
        return r.json().get("promotionChannels", {})
    return {}

def get_friends_by_identifier(identifier, limit=500):
    uid = identifier if identifier.isdigit() else search_by_username(identifier)
    if not uid:
        return {"error": "User not found"}
    return get_entity_list(uid, "friends", limit=limit)

def get_user_info(identifier, use_cache=True, **options):
    limit = options.get("limit", 500)
    cached = read_cache(identifier)
    if cached:
        return cached

    uid = identifier if identifier.isdigit() else search_by_username(identifier)
    if not uid:
        return {"error": "User not found"}

    url = f"https://users.roblox.com/v1/users/{uid}"
    headers = {"User-Agent": get_user_agent()}
    r, _ = try_request("get", url, headers=headers)
    if not r or r.status_code != 200:
        return {"error": "Failed to fetch profile"}

    base = r.json()
    data = {
        "user_id": uid,
        "alias": base.get("name"),
        "display_name": base.get("displayName"),
        "description": base.get("description"),
        "is_banned": base.get("isBanned"),
        "has_verified_badge": base.get("hasVerifiedBadge"),
        "join_date": base.get("created")
    }

    try:
        dt = datetime.fromisoformat(base["created"].replace("Z", "+00:00"))
        diff = datetime.now(timezone.utc) - dt
        years = diff.days // 365
        days = diff.days % 365
        data["account_age"] = f"{years} Years, {days} Days"
    except:
        data["account_age"] = "Unknown"

    def count(url):
        r, _ = try_request("get", url, headers=headers)
        return r.json().get("count", 0) if r and r.status_code == 200 else 0

    data["friends"] = count(f"https://friends.roblox.com/v1/users/{uid}/friends/count")
    data["followers"] = count(f"https://friends.roblox.com/v1/users/{uid}/followers/count")
    data["following"] = count(f"https://friends.roblox.com/v1/users/{uid}/followings/count")

    tasks = [
        ("previous_usernames", get_previous_usernames, [uid]),
        ("groups", get_groups, [uid]),
        ("about_me", get_about_me, [uid]),
        ("friends_list", get_entity_list, [uid, "friends", limit]),
        ("followers_list", get_entity_list, [uid, "followers", limit]),
        ("following_list", get_entity_list, [uid, "followings", limit]),
        ("presence", get_presence, [uid]),
        ("roblox_badges", get_badges, [uid]),
        ("promotion_channels", get_promo_channels, [uid])
    ]

    results = run_multi(tasks)

    for k, v in results.items():
        data[k] = v

    p = results["presence"]
    if p:
        data["presence_status"] = USER_PRESENCE_MAP.get(p["userPresenceType"])
        data["last_location"] = p.get("lastLocation")
        data["current_place_id"] = p.get("placeId")
        data["last_online_timestamp"] = p.get("lastOnline")
    else:
        data["presence_status"] = "Unknown"

    write_cache(identifier, data)
    return data
