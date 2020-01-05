import aiohttp

BASE_URL = "https://twitter.com/"
USER_LOOKUP_API_URL = "https://api.twitter.com/1.1/users/lookup.json"
USER_TIMELINE_API_URL = "https://api.twitter.com/1.1/statuses/user_timeline.json"


class TwitterClient:
    def __init__(self):
        with open("keystokens/twitter/bearer_token", "r") as bearer_token_file:
            bearer_token = bearer_token_file.read()
            self.headers = {"Authorization": "Bearer " + bearer_token}
        self.client_session = aiohttp.ClientSession()

    async def valid_username(self, username: str) -> bool:
        """Checks if Twitter account with given username exists"""
        async with self.client_session.get(BASE_URL + username, headers=self.headers) as response:
            return response.status == 200

    async def get_user(self, username: str):
        """Gets user information by username"""
        async with self.client_session.get(USER_LOOKUP_API_URL + "?screen_name=" + username, headers=self.headers) as response:
            if response.status == 200:
                user_json = await response.json()
                return user_json[0]
            else:
                return None

    async def get_timeline(self, username: str):
        """Gets user tweets by username"""
        async with self.client_session.get(USER_TIMELINE_API_URL + "?screen_name=" + username, headers=self.headers) as response:
            timeline = await response.json()
            return timeline