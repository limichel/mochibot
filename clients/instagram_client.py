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
        async with self.client_session.get(BASE_URL + username) as response:
            if response.status != 200:
                return {}
            while not response.content.at_eof():
                line = await response.content.readline()
                if b'window._sharedData = ' in line:
                    str_line = str(line)
                    data_str = str_line.split("window._sharedData = ")[1].split(";")[0]
                    data = json.loads(data_str.replace("\\", ""))  # Remove escape character to avoid parsing error
                    return {"username": data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["username"],
                            "user_id": data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["id"]}
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
