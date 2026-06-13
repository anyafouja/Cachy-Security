import discord
from discord.ext import commands
import aiohttp
import asyncio

BASE = 'https://users.roblox.com/v1'
THUMB = 'https://thumbnails.roblox.com/v1'
FRIENDS = 'https://friends.roblox.com/v1'
PRESENCE = 'https://presence.roblox.com/v1'

COLOR = 0xED4245


class Roblox(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    async def _get(self, url, params=None):
        for attempt in range(3):
            try:
                async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status == 429:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    if r.status == 200:
                        return await r.json()
            except Exception:
                if attempt == 2:
                    raise
                await asyncio.sleep(1)
        return None

    async def _post(self, url, json_body):
        for attempt in range(3):
            try:
                async with self.session.post(url, json=json_body, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status == 429:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    if r.status == 200:
                        return await r.json()
            except Exception:
                if attempt == 2:
                    raise
                await asyncio.sleep(1)
        return None

    async def search_user(self, username):
        data = await self._get(f'{BASE}/users/search', params={'keyword': username, 'limit': 10})
        if not data:
            return None
        entries = data.get('data')
        if not entries:
            return None
        for u in entries:
            if u['name'].lower() == username.lower():
                return u
        return entries[0]

    async def get_user_info(self, user_id):
        return await self._get(f'{BASE}/users/{user_id}')

    async def get_avatar(self, user_id):
        data = await self._get(f'{THUMB}/users/avatar-headshot', params={'userIds': str(user_id), 'size': '720x720', 'format': 'Png'})
        if data and data.get('data'):
            return data['data'][0].get('imageUrl')
        return None

    async def get_followers(self, user_id):
        data = await self._get(f'{FRIENDS}/users/{user_id}/followers/count')
        if data:
            return data.get('count', 0)
        return 0

    async def get_following(self, user_id):
        data = await self._get(f'{BASE}/users/{user_id}/followings/count')
        if data:
            return data.get('count', 0)
        return 0

    async def get_friends(self, user_id):
        data = await self._get(f'{FRIENDS}/users/{user_id}/friends/count')
        if data:
            return data.get('count', 0)
        return 0

    async def get_status(self, user_id):
        data = await self._get(f'{BASE}/users/{user_id}/status')
        if data:
            return data.get('status') or None
        return None

    async def get_presence(self, user_id):
        data = await self._post(f'{PRESENCE}/presence/users', {'userIds': [user_id]})
        if data and data.get('userPresences'):
            return data['userPresences'][0].get('userPresenceType', 0)
        return 0

    @commands.hybrid_command(name='roblox', description='Search Roblox user profile')
    async def roblox_profile(self, ctx: commands.Context, username: str):
        await ctx.defer()
        user = await self.search_user(username)
        if not user:
            await ctx.send(embed=discord.Embed(description=f'User **{username}** tidak ditemukan.', color=COLOR))
            return
        uid = user['id']
        name = user['name']
        display = user.get('displayName', name)
        info = await self.get_user_info(uid)
        avatar_url = await self.get_avatar(uid)
        followers = await self.get_followers(uid)
        following = await self.get_following(uid)
        friends_count = await self.get_friends(uid)
        status = await self.get_status(uid)
        presence = await self.get_presence(uid)

        embed = discord.Embed(color=COLOR)
        embed.set_author(name=f'{display} (@{name})', url=f'https://www.roblox.com/users/{uid}/profile')
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)
        if info:
            desc = info.get('description', '')
            if desc:
                embed.description = desc[:200]
        status_text = {0: 'Offline', 1: 'Online', 2: 'In Game', 3: 'Studio'}.get(presence, 'Unknown')
        embed.add_field(name='Followers', value=f'{followers:,}')
        embed.add_field(name='Following', value=f'{following:,}')
        embed.add_field(name='Friends', value=f'{friends_count:,}')
        embed.add_field(name='Status', value=status_text)
        if status:
            embed.add_field(name='Status Message', value=status[:100], inline=False)
        if info and info.get('created'):
            created = discord.utils.format_dt(discord.utils.parse_time(info['created'].replace('Z', '+00:00')), 'R')
            embed.add_field(name='Joined Roblox', value=created)
        if info and info.get('isBanned'):
            embed.add_field(name='Banned', value='Yes')
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Roblox(bot))
