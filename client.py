from discord.ext import commands

from modules.twitter import Twitter

description = "Mochi Bot"

bot = commands.Bot(command_prefix=".", description=description)
bot.add_cog(Twitter(bot))


@bot.event
async def on_ready():
    print("Logged in as", bot.user.name)
    print(bot.user.id)

@bot.command()
async def echo(ctx, text: str):
    await ctx.send(text)

bot.run("NjIxNTc5OTYxNzgxODQ2MDI1.XZlGvg.3-kE_eJBM2gCHKDos7K2nSNc47M")