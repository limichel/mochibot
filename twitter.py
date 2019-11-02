import discord
from discord.ext import commands, tasks
from pymongo import MongoClient

import twitter_functions


class Twitter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_collection = MongoClient("localhost:27017").mochibot.twitter
        # self.check_for_new_tweets.start()

    @commands.group()
    async def twitter(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command")

    @twitter.command()
    async def add(self, ctx, username: str, channel: discord.TextChannel):
        if twitter_functions.valid_username(username):
            user = twitter_functions.get_user(username)
            if user:
                self._add_new_user(user["screen_name"], user["id"], user["status"]["id"],
                                   ctx.guild.id, channel.id)
                await ctx.send("Added {}".format(user["screen_name"]))
        else:
            await ctx.send("Invalid username")

    @tasks.loop(seconds = 30.0)
    async def check_for_new_tweets(self):
        for user in self.db_collection.find():
            print("checking ", user)
            timeline = twitter_functions.get_timeline(user["username"])
            new_tweet_ids = []
            i = 0
            while timeline[i]["id"] != user["last_tweet"]:
                new_tweet_ids.append(timeline[i]["id"])
                i += 1
            if len(new_tweet_ids) > 0:
                user["last_tweet"] = new_tweet_ids[0]
                self.db_collection.update_one({"_id": user.get("_id")}, {"$set": {"last_tweet": new_tweet_ids[0]}})
                while len(new_tweet_ids) != 0:
                    for subscriber in user["subscribers"]:
                        channel = self.bot.get_channel(subscriber["channel"])
                        await channel.send("https://twitter.com/{}/status/{}".format(user["username"], new_tweet_ids.pop(0)))

    # Database methods
    def _add_new_user(self, username, user_id, most_recent_status_id, server, channel):
        user = {
            "username": username,
            "user_id": user_id,
            "last_tweet": most_recent_status_id,
            "subscribers": []
        }
        user["subscribers"].append({"server": server, "channel": channel})
        self.db_collection.insert_one(user)