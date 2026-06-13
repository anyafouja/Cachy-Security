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
    print(f'Online: {bot.user} ({bot.user.id}) in {len(bot.guilds)} guilds')
    for guild in bot.guilds:
        try:
            await bot.tree.sync(guild=guild)
            print(f'Synced guild {guild.id}')
        except Exception as e:
            print(f'Sync failed for {guild.id}: {e}')
    await bot.tree.sync()
    print('Startup sync done')

@bot.hybrid_command(name='help', description='Show all commands')
async def help_cmd(ctx: commands.Context):
    embed = discord.Embed(title='Cachy Security Bot', color=0xED4245)
    embed.add_field(name='/roblox <username>', value='Search Roblox profile', inline=False)
    embed.add_field(name='/filteradd <word>', value='Add word to filter', inline=False)
    embed.add_field(name='/filterremove <word>', value='Remove word from filter', inline=False)
    embed.add_field(name='/filterlist', value='Show all banned words', inline=False)
    embed.add_field(name='/whitelist', value='Toggle whitelist for this channel', inline=False)
    embed.add_field(name='/filterstats', value='Show security stats', inline=False)
    embed.add_field(name='/sync', value='Sync slash commands (admin only)', inline=False)
    embed.set_footer(text='Some commands require Manage Messages permission')
    await ctx.send(embed=embed)

@bot.hybrid_command(name='sync', description='Sync slash commands manually')
@commands.has_permissions(administrator=True)
async def sync_cmd(ctx: commands.Context):
    await ctx.defer(ephemeral=True)
    try:
        await bot.tree.sync(guild=ctx.guild)
        await ctx.send('Synced!', ephemeral=True)
    except Exception as e:
        await ctx.send(f'Error: {e}', ephemeral=True)

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
