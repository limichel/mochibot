import discord
import logging
import os
from os.path import abspath, dirname
from datetime import datetime, timezone
from discord.ext import commands, tasks
from pymongo import MongoClient

from clients.instagram_client import InstagramClient

class Instagram(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_collection = MongoClient("localhost:27017").mochibot.instagram
        self.client = InstagramClient()

        self.logger = self._configure_logger()

    @commands.group()
    async def ig(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command")

    @ig.command()
    async def add(self, ctx, username: str, channel: discord.TextChannel):
        user = await self.client.get_user(username)
        if len(user) != 0:
            self._add_user(user["username"], user["user_id"], ctx.guild.id, channel.id)
            await ctx.send("Added {} to Instagram subscriptions.".format(user["username"]))
        else:
            await ctx.send("Invalid username.")

    @ig.command()
    async def remove(self, ctx, username: str):
        user = self.db_collection.find_one({"username": username, "subscribers": {"$elemMatch": {"server": ctx.guild.id}}})
        if user:
            if len(user["subscribers"]) == 1:
                self.db_collection.delete_one({"username": username})
            else:
                self.db_collection.update_one({"username": username},
                    {"$pull": {"subscribers": {"server": ctx.guild.id}}}
                )
            await ctx.send("Removed {} feed from Instagram subscriptions.".format(username))
        else:
            await ctx.send("Invalid username.")

    @ig.command()
    async def list(self, ctx):
        response = ["Active Instagram feed subscriptions:"]
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

    @tasks.loop(seconds=60.0)
    async def check_for_new_posts(self):
        try:
            for user in self.db_collection.find():
                print("checking ", user)
                last_check_time = datetime.now(timezone.utc)
                posts = self.client.get_posts(user["user_id"])
                new_post_shortcodes = []
                for post in posts:
                    post_time = datetime.fromtimestamp(post["taken_at_timestamp"], timezone.utc)
                    if post_time < user["last_check_time"].replace(tzinfo=timezone.utc):
                        break
                    new_post_shortcodes.append(post["shortcode"])
                    if len(new_post_shortcodes) > 0:
                        while len(new_post_shortcodes) != 0:
                            for subscriber in user["subscribers"]:
                                channel = self.bot.get_channel(subscriber["channel"])
                                await channel.send("https://instagram.com/p/{}".format(new_post_shortcodes.pop(0)))
                self.db_collection.update_one({"_id": user.get("_id")}, {"$set": {"last_check_time": last_check_time}})
        except Exception as e:
            self.logger.error(e)


    # Database methods
    def _add_user(self, username, user_id, server, channel):
        user = self.db_collection.find_one({"username": username})
        if user is None:
            user = {
                "username": username,
                "user_id": user_id,
                "last_check_time": datetime.now(timezone.utc),
                "subscribers": [{"server": server, "channel": channel}]
            }
            self.db_collection.insert_one(user)
        else:
            self.db_collection.update_one({"_id": user["_id"]}, {"$push": {"server": server, "channel": channel}})

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