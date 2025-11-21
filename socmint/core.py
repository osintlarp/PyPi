import json

class socmintPY:
    def __init__(self):
        pass

    def get_user_basic_details(self, identifier, pretty_print=False, service=None, **options):
        if service is None:
            raise ValueError("Specify a service module such as socmint.roblox.")
        data = service.get_user_info(identifier, **options)
        if pretty_print:
            print(json.dumps(data, indent=4, ensure_ascii=False))
        return data

    def get_user_friends(self, identifier, pretty_print=False, service=None):
        if service is None:
            raise ValueError("Specify a service module such as socmint.roblox.")
        
        data = service.get_friends_by_identifier(identifier)
        
        if pretty_print:
            print(json.dumps(data, indent=4, ensure_ascii=False))
        return data

