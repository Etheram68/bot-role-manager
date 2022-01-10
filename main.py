#!/mnt/e/Projet_perso/Bot-Discord/auto-give-role/.venv/bin/python
import discord
import sys, traceback, os
from discord.ext import commands

intents = discord.Intents().all()
activity = discord.Game(name="Assign Roles")

bot = commands.Bot(command_prefix='>', intents=intents, activity=activity)
bot.remove_command("help")

initial_extension = ['src.cogs.role']

if __name__ == '__main__':
    for extension in initial_extension:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(f'Failed to load extension {extension}.', file=sys.stderr)
            traceback.print_exc()

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

bot.run(os.environ['DISCORD_TOKEN'])
