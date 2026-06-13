import re
import os
import json
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
import discord
from discord.ext import commands

SPAM_WINDOW = 5
SPAM_THRESHOLD = 5
RAID_WINDOW = 30
RAID_THRESHOLD = 5
INVITE_RE = re.compile(r'(?:discord\.(?:gg|io|me|com\/invite)\/[\w-]+)', re.I)
DATA_FILE = 'security_data.json'

def load_data():
    if os.path.isfile(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {'banned_words': [], 'whitelisted_channels': []}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)


class Security(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_log = defaultdict(list)
        self.join_log = defaultdict(list)
        self.raid_alerted = set()
        self.data = load_data()
        self.banned_words = self.data.get('banned_words', [])
        self.whitelisted = self.data.get('whitelisted_channels', [])

    async def safe_delete(self, msg, delay=0):
        try:
            await msg.delete(delay=delay)
        except Exception:
            pass

    async def warn(self, msg, text, delete_after=8):
        try:
            embed = discord.Embed(description=text, color=0xED4245)
            m = await msg.channel.send(embed=embed)
            await m.delete(delay=delete_after)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot or not msg.guild:
            return
        if msg.channel.id in self.whitelisted:
            return

        uid = msg.author.id
        now = datetime.utcnow()
        self.spam_log[uid].append(now)
        self.spam_log[uid] = [t for t in self.spam_log[uid] if t > now - timedelta(seconds=SPAM_WINDOW)]
        if len(self.spam_log[uid]) > SPAM_THRESHOLD:
            await self.safe_delete(msg)
            await self.warn(msg, f'{msg.author.mention} jangan spam!')
            return

        if INVITE_RE.search(msg.content):
            await self.safe_delete(msg)
            await self.warn(msg, f'{msg.author.mention} dilarang kirim invite link!')
            return

        if self.banned_words:
            lower = msg.content.lower()
            for word in self.banned_words:
                if word in lower:
                    await self.safe_delete(msg)
                    await self.warn(msg, f'{msg.author.mention} pesan mengandung kata terlarang!')
                    return

    @commands.Cog.listener()
    async def on_member_join(self, member):
        gid = member.guild.id
        now = datetime.utcnow()
        self.join_log[gid].append(now)
        self.join_log[gid] = [t for t in self.join_log[gid] if t > now - timedelta(seconds=RAID_WINDOW)]
        if len(self.join_log[gid]) > RAID_THRESHOLD and gid not in self.raid_alerted:
            self.raid_alerted.add(gid)
            log_ch = discord.utils.get(member.guild.text_channels, name='mod-log')
            if log_ch:
                embed = discord.Embed(
                    title='Potential Raid Detected',
                    description=f'{len(self.join_log[gid])} joins in {RAID_WINDOW}s',
                    color=0xED4245
                )
                await log_ch.send(embed=embed)
            await asyncio.sleep(120)
            self.raid_alerted.discard(gid)

    @commands.hybrid_command(name='filteradd', description='Add word to filter')
    @commands.has_permissions(manage_messages=True)
    async def filter_add(self, ctx: commands.Context, word: str):
        word = word.lower().strip()
        if word in self.banned_words:
            await ctx.send('already in filter', ephemeral=True)
            return
        self.banned_words.append(word)
        self.data['banned_words'] = self.banned_words
        save_data(self.data)
        await ctx.send(f'`{word}` added to filter')

    @commands.hybrid_command(name='filterremove', description='Remove word from filter')
    @commands.has_permissions(manage_messages=True)
    async def filter_remove(self, ctx: commands.Context, word: str):
        word = word.lower().strip()
        if word not in self.banned_words:
            await ctx.send('not in filter', ephemeral=True)
            return
        self.banned_words.remove(word)
        self.data['banned_words'] = self.banned_words
        save_data(self.data)
        await ctx.send(f'`{word}` removed from filter')

    @commands.hybrid_command(name='filterlist', description='Show all banned words')
    @commands.has_permissions(manage_messages=True)
    async def filter_list(self, ctx: commands.Context):
        if not self.banned_words:
            await ctx.send('filter is empty')
            return
        await ctx.send('banned words: ' + ', '.join(f'`{w}`' for w in self.banned_words))

    @commands.hybrid_command(name='whitelist', description='Toggle whitelist for this channel')
    @commands.has_permissions(manage_messages=True)
    async def filter_whitelist(self, ctx: commands.Context):
        cid = ctx.channel.id
        if cid in self.whitelisted:
            self.whitelisted.remove(cid)
            await ctx.send('channel removed from whitelist')
        else:
            self.whitelisted.append(cid)
            await ctx.send('channel added to whitelist')
        self.data['whitelisted_channels'] = self.whitelisted
        save_data(self.data)

    @commands.hybrid_command(name='filterstats', description='Show security stats')
    @commands.has_permissions(manage_messages=True)
    async def filter_stats(self, ctx: commands.Context):
        embed = discord.Embed(title='Security Stats', color=0x5865F2)
        embed.add_field(name='Banned Words', value=str(len(self.banned_words)))
        embed.add_field(name='Whitelisted Channels', value=str(len(self.whitelisted)))
        embed.add_field(name='Active Spam Trackers', value=str(len(self.spam_log)))
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Security(bot))
