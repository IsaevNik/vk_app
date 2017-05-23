import json


def get_user_info(api_data):
    response = json.loads(api_data).get('response')
    if response:
        try:
            return response[0]
        except (TypeError, IndexError):
            pass
    return None

