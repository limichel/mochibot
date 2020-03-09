from discord.ext import commands

from modules.twitter import Twitter
from modules.instagram import Instagram

with open("keystokens/discord/bot_token", "r") as bot_token_file:
    BOT_TOKEN = bot_token_file.read()

description = "Mochi Bot"

bot = commands.Bot(command_prefix=".", description=description)
bot.add_cog(Twitter(bot))
bot.add_cog(Instagram(bot))


@bot.event
async def on_ready():
    print("Logged in as", bot.user.name)
    print(bot.user.id)

@bot.command()
async def echo(ctx, text: str):
    await ctx.send(text)

bot.run(BOT_TOKEN)