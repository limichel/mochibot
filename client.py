from discord.ext import commands

from modules.twitter import Twitter
from modules.instagram import Instagram

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

# dev token: Njc2MzIzNzY0NzY5NzgzODE4.XmWeJQ.P0sawPQ-W8GPT79_MaDrC4qXmx8
# token: NjIxNTc5OTYxNzgxODQ2MDI1.XmWdEg.uHoER1kvcOvm9_RKJPQN6pIPcDU
bot.run("NjIxNTc5OTYxNzgxODQ2MDI1.XmWdEg.uHoER1kvcOvm9_RKJPQN6pIPcDU")