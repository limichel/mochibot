import aiohttp
import json

BASE_URL = "https://www.instagram.com/"
USER_QUERY_URL = "https://www.instagram.com/graphql/query/"
QUERY_HASH = "e769aa130647d2354c40ea6a439bfc08"

class InstagramClient:
    def __init__(self):
        self.client_session = aiohttp.ClientSession()

    async def get_user(self, username: str) -> tuple:
        """Gets username and id of user with given username"""
        async with self.client_session.get(BASE_URL + username + "?__a=1") as response:
            if response.status == 200:
                user_json = await response.json()
                return {"username": user_json["graphql"]["user"]["username"],
                        "user_id": user_json["graphql"]["user"]["id"]}
            return {}

    async def get_posts(self, user_id: str):
        variables = {"id": user_id, "first": 10}
        url = USER_QUERY_URL + "?query_hash={}&variables={}".format(QUERY_HASH, json.dumps(variables))
        posts = []
        async with self.client_session.get(url) as response:
            feed = await response.json()
            for post in feed["data"]["user"]["edge_owner_to_timeline_media"]["edges"]:
                posts.append(post["node"]) # NOTE: timestamp is UNIX timestamp --> seconds
        return posts
