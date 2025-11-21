import json
import os
import sys
import requests
from .cprint import success, error
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
            error("Please provide a valid cookie in config.COOKIES['roblox_account_token'].")
            if sys.platform == 'win32':
                os.system("pause")
            sys.exit(0)

        try:
            url = "https://users.roblox.com/v1/users/authenticated"
            headers = {"User-Agent": "Roblox/WinInet"} 
            
            response = requests.get(
                url, 
                cookies={".ROBLOSECURITY": cookie},
                verify=config.VERIFY_SSL,
                timeout=config.TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                self.logged_in_user = data.get("name")
                self.logged_in_uid = data.get("id")
                success(f"Logged in {self.logged_in_user}!")
            else:
                error("Invalid cookie.")
                if sys.platform == 'win32':
                    os.system("pause")
                sys.exit(0)

        except Exception as e:
            error(f"Login check failed: {e}")
            if sys.platform == 'win32':
                os.system("pause")
            sys.exit(0)

    def get_user_basic_details(self, identifier, pretty_print=False, service=None, **options):
        if service is None:
            raise ValueError("Specify a service module such as socmint.roblox.")
        
        data = service.get_user_info(identifier, **options)
        
        if pretty_print:
            print(json.dumps(data, indent=4, ensure_ascii=False))
        return data

    def get_user_friends(self, identifier, pretty_print=False, service=None, limit=500):
        if service is None:
            raise ValueError("Specify a service module such as socmint.roblox.")
        
        data = service.get_friends_by_identifier(identifier, limit=limit)
        
        if pretty_print:
            print(json.dumps(data, indent=4, ensure_ascii=False))
        return data

    def report_user(self, username, pretty_print=True, service=None, total_reports=5):
        if not self.logged_in_user:
            error("You must initialize socmintPY(use_account=True) and set config.COOKIES to use this feature.")
            return

        if service is None:
            raise ValueError("Specify a service module such as socmint.roblox.")

        cookie = config.COOKIES.get("roblox_account_token")
        service.report_user(username, cookie, self.logged_in_uid, total_reports=total_reports)
