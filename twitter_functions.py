import requests

BASE_URL = "https://twitter.com/"
USER_LOOKUP_API_URL = "https://api.twitter.com/1.1/users/lookup.json"
USER_TIMELINE_API_URL = "https://api.twitter.com/1.1/statuses/user_timeline.json"

with open("keystokens/twitter/bearer_token", "r") as bearer_token_file:
    bearer_token = bearer_token_file.read()


def valid_username(username: str) -> bool:
    """Checks if Twitter account with given username exists"""
    response = requests.get(BASE_URL + username)
    return response.status_code == 200

def get_user(username: str):
    """Gets user information"""
    response = requests.get(USER_LOOKUP_API_URL + "?screen_name=" + username,
                            headers={"Authorization": "Bearer " + bearer_token})
    if response.status_code == 200:
        user = response.json()[0]
        return user
    else:
        return None

def get_timeline(username: str):
    url = USER_TIMELINE_API_URL + "?screen_name=" + username
    response = requests.get(url, headers={"Authorization": "Bearer " + bearer_token})
    timeline = response.json()
    return timeline