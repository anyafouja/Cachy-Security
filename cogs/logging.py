import os
import discord
from discord.ext import commands

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def log_channel_ids(self):
        raw = os.getenv('LOG_CHANNEL_IDS', '')
        return [int(x) for x in raw.split(',') if x.strip().isdigit()]

    def get_log_channel(self, guild):
        for cid in self.log_channel_ids:
            ch = guild.get_channel(cid)
            if ch:
                return ch
        return discord.utils.get(guild.text_channels, name='mod-log')

    @commands.Cog.listener()
    async def on_message_delete(self, msg):
        if msg.author.bot or not msg.guild:
            return
        ch = self.get_log_channel(msg.guild)
        if not ch:
            return
        embed = discord.Embed(
            title='Message Deleted',
            color=0xED4245,
            timestamp=msg.created_at
        )
        embed.set_author(name=msg.author.display_name, icon_url=msg.author.display_avatar.url)
        embed.add_field(name='Channel', value=msg.channel.mention)
        if msg.content:
            embed.add_field(name='Content', value=msg.content[:1000], inline=False)
        if msg.attachments:
            embed.add_field(name='Attachments', value='\n'.join(a.url for a in msg.attachments[:5]), inline=False)
        await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or not before.guild:
            return
        if before.content == after.content:
            return
        ch = self.get_log_channel(before.guild)
        if not ch:
            return
        embed = discord.Embed(
            title='Message Edited',
            color=0xFEE75C,
            timestamp=before.edited_at or discord.utils.utcnow()
        )
        embed.set_author(name=before.author.display_name, icon_url=before.author.display_avatar.url)
        embed.add_field(name='Channel', value=before.channel.mention)
        embed.add_field(name='Before', value=before.content[:500] or '*no text*', inline=False)
        embed.add_field(name='After', value=after.content[:500] or '*no text*', inline=False)
        msg_link = f'https://discord.com/channels/{before.guild.id}/{before.channel.id}/{before.id}'
        embed.add_field(name='Jump', value=f'[link]({msg_link})', inline=False)
        await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        ch = self.get_log_channel(member.guild)
        if not ch:
            return
        embed = discord.Embed(
            title='Member Joined',
            description=f'{member.mention} {member.display_name}',
            color=0x57F287
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name='Account Created', value=discord.utils.format_dt(member.created_at, 'R'))
        embed.add_field(name='Member Count', value=str(member.guild.member_count))
        await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        ch = self.get_log_channel(member.guild)
        if not ch:
            return
        embed = discord.Embed(
            title='Member Left',
            description=f'{member.mention} {member.display_name}',
            color=0xED4245
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name='Joined At', value=discord.utils.format_dt(member.joined_at, 'R') if member.joined_at else 'Unknown')
        embed.add_field(name='Member Count', value=str(member.guild.member_count))
        await ch.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Logging(bot))
