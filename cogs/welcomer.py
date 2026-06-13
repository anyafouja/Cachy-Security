import os
import discord
from discord.ext import commands

class Welcomer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_welcome_channel(self, guild):
        cid = os.getenv('WELCOME_CHANNEL_ID')
        if cid and cid.isdigit():
            ch = guild.get_channel(int(cid))
            if ch:
                return ch
        return discord.utils.get(guild.text_channels, name='welcome')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        ch = self.get_welcome_channel(member.guild)
        if not ch:
            return
        embed = discord.Embed(
            description=f'Selamat datang {member.mention} di **{member.guild.name}**!',
            color=0x57F287
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f'Member #{member.guild.member_count}')
        try:
            await ch.send(embed=embed)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        ch = self.get_welcome_channel(member.guild)
        if not ch:
            return
        embed = discord.Embed(
            description=f'{member.display_name} telah meninggalkan server.',
            color=0xED4245
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        try:
            await ch.send(embed=embed)
        except Exception:
            pass


async def setup(bot):
    await bot.add_cog(Welcomer(bot))
