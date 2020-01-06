import discord
import logging
import os
from os.path import abspath, dirname
from datetime import datetime, timezone
from discord.ext import commands, tasks
from pymongo import MongoClient

from clients.twitter_client import TwitterClient


class Twitter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_collection = MongoClient("localhost:27017").mochibot.twitter
        self.twitter_client = TwitterClient()
        self.check_for_new_tweets.start()

        self.logger = self._configure_logger()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(str(error))
        else:
            self.logger.error(error)

    @commands.group()
    async def twitter(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command")

    @twitter.command()
    async def add(self, ctx, username: str, channel: discord.TextChannel):
        if await self.twitter_client.valid_username(username):
            user = await self.twitter_client.get_user(username)
            if user:
                self._add_new_user(user["screen_name"], user["id"], user["status"]["id"],
                                   ctx.guild.id, channel.id)
                await ctx.send("Added {} to Twitter subscriptions.".format(user["screen_name"]))
        else:
            await ctx.send("Invalid username.")

    @twitter.command()
    async def remove(self, ctx, username: str):
        user = self.db_collection.find_one({"username": username, "subscribers": {"$elemMatch": {"server": ctx.guild.id}}})
        if user:
            if len(user["subscribers"]) == 1:
                self.db_collection.delete_one({"username": username})
            else:
                self.db_collection.update_one({"username": username},
                    {"$pull": {"subscribers": {"server": ctx.guild.id}}}
                )
            await ctx.send("Removed {} feed from Twitter subscriptions.".format(username))
        else:
            await ctx.send("Invalid username.")

    @twitter.command()
    async def list(self, ctx):
        response = ["Active Twitter feed subscriptions:"]
        users = list(self.db_collection.aggregate([
            {"$match": {
                "subscribers.server": ctx.guild.id
            }},
            {"$project": {"username": 1, "subscribers": {
                "$filter": {
                    "input": "$subscribers",
                    "as": "subscribers",
                    "cond": {"$eq": ["$$subscribers.server", ctx.guild.id]}
                }}}
             }
        ]))

        for user in users:
            response.append("\t {} -> <#{}>".format(user["username"], user["subscribers"][0]["channel"]))
        if len(users) == 0:
            response.append("\t None")
        await ctx.send("\n".join(response))




    @tasks.loop(seconds = 60.0)
    async def check_for_new_tweets(self):
        for user in self.db_collection.find():
            print("checking ", user)
            last_check_time = datetime.now(timezone.utc)
            timeline = await self.twitter_client.get_timeline(user["username"])
            new_tweet_ids = []
            for tweet in timeline:
                tweet_time = datetime.strptime(tweet["created_at"], "%a %b %d %H:%M:%S %z %Y")
                if tweet_time < user["last_check_time"].replace(tzinfo=timezone.utc):
                    break
                new_tweet_ids.append(tweet["id"])
            if len(new_tweet_ids) > 0:
                while len(new_tweet_ids) != 0:
                    for subscriber in user["subscribers"]:
                        channel = self.bot.get_channel(subscriber["channel"])
                        await channel.send("https://twitter.com/{}/status/{}".format(user["username"], new_tweet_ids.pop(0)))
            self.db_collection.update_one({"_id": user.get("_id")}, {"$set": {"last_check_time": last_check_time}})

    @check_for_new_tweets.before_loop
    async def before_check_for_new_tweets(self):
        await self.bot.wait_until_ready()

    # Database methods
    def _add_new_user(self, username, user_id, most_recent_status_id, server, channel):
        user = {
            "username": username,
            "user_id": user_id,
            "last_check_time": datetime.now(timezone.utc),
            "subscribers": []
        }
        user["subscribers"].append({"server": server, "channel": channel})
        self.db_collection.insert_one(user)

    # __init__ helper methods
    def _configure_logger(self):
        logger = logging.getLogger(__name__)
        log_directory = os.path.join(dirname(dirname(abspath(__file__))), "logs")
        if not os.path.isdir(log_directory):
            os.makedirs(log_directory)
        error_handler = logging.FileHandler(os.path.join(log_directory, ("error_{}.log".format(__name__))))
        error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(error_formatter)
        # TODO: debug level logging
        logger.addHandler(error_handler)
        return logger
