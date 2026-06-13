import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise SystemExit('DISCORD_TOKEN not set')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'Online: {bot.user} ({bot.user.id})')

async def main():
    async with bot:
        await bot.load_extension('cogs.security')
        await bot.load_extension('cogs.logging')
        await bot.load_extension('cogs.welcomer')
        await bot.load_extension('cogs.roblox')
        await bot.start(TOKEN)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
