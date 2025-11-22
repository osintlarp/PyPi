import json
import os
import sys
import requests
from .cprint import success, error, info
from . import config

class socmintPY:
    def __init__(self, use_account=False):
        self.logged_in_user = None
        self.logged_in_uid = None
        if use_account:
            self.check_login()

    def check_login(self):
        cookie = config.COOKIES.get("roblox_account_token")
        if not cookie:
            error("Please provide a valid cookie")
            sys.exit(0)
        try:
            url = "https://users.roblox.com/v1/users/authenticated"
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Cookie": f".ROBLOSECURITY={cookie}"
            }
            r = requests.get(url, headers=headers, timeout=config.TIMEOUT, verify=config.VERIFY_SSL)
            if r.status_code == 200:
                d = r.json()
                self.logged_in_user = d.get("name")
                self.logged_in_uid = d.get("id")
                success(f"Logged in as {self.logged_in_user} ({self.logged_in_uid})")
            else:
                error("Invalid cookie")
                sys.exit(0)
        except Exception as e:
            error(str(e))
            sys.exit(0)

    def get_user_basic_details(self, identifier, pretty_print=False, service=None, **options):
        data = service.get_user_info(identifier, **options)
        if pretty_print:
            print(json.dumps(data, indent=4, ensure_ascii=False))
        return data

    def get_user_friends(self, identifier, pretty_print=False, service=None, limit=500):
        data = service.get_friends_by_identifier(identifier, limit=limit)
        if pretty_print:
            print(json.dumps(data, indent=4, ensure_ascii=False))
        return data

    def report_user(self, username, pretty_print=True, service=None, total_reports=5):
        cookie = config.COOKIES.get("roblox_account_token")
        service.report_user(username, cookie, self.logged_in_uid, total_reports=total_reports)
