import requests
import random
import urllib3
from .cprint import info, error, success
from . import config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X)"
]

def get_user_agent():
    ua = random.choice(USER_AGENTS)
    info(f"Selected User-Agent: {ua}")
    return ua

def try_request(method, url, headers=None, cookies=None, json_payload=None):
    info(f"Request: {method.upper()} {url}")

    if not config.VERIFY_SSL:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    try:
        r = requests.request(
            method,
            url,
            headers=headers,
            cookies=cookies,
            json=json_payload,
            timeout=config.TIMEOUT,
            proxies=config.PROXY,
            verify=config.VERIFY_SSL
        )
        success(f"Response {r.status_code} from {url}")
        return r, None
    except Exception as e:
        error(f"Request failed: {e}")
        return None, str(e)

