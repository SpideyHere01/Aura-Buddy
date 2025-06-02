import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import aiohttp
from typing import Optional
import time

class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_users = {}

    @commands.command(name='afk', help='Set yourself as AFK with a reason')
    async def afk_command(self, ctx, *, reason=None):
        await self.afk_logic(ctx, reason)

    @app_commands.command(name='afk', description='Set yourself as AFK with a reason')
    async def afk_slash(self, interaction: discord.Interaction, reason: str = None):
        await self.afk_logic(interaction, reason)

    async def afk_logic(self, ctx, reason=None):
        user_id = ctx.author.id if isinstance(ctx, commands.Context) else ctx.user.id
        if user_id in self.afk_users:
            await self.send_response(ctx, "You are already AFK! Use `.back` to remove AFK status.")
            return

        reason = "AFK" if reason is None else reason
        if len(reason) > 100:
            await self.send_response(ctx, "Your AFK reason is too long! Please keep it under 100 characters.")
            return

        self.afk_users[user_id] = {
            "reason": reason,
            "time": int(time.time())
        }

        user = ctx.author if isinstance(ctx, commands.Context) else ctx.user
        await self.send_response(ctx, f"🌙 **{user.name}** is now AFK: {reason}")

    @commands.command(name='back', help='Remove your AFK status')
    async def back_command(self, ctx):
        await self.back_logic(ctx)

    @app_commands.command(name='back', description='Remove your AFK status')
    async def back_slash(self, interaction: discord.Interaction):
        await self.back_logic(interaction)

    def get_afk_duration(self, start_time):
        duration = int(time.time()) - start_time
        if duration < 60:
            return f"{duration}s"
        elif duration < 3600:
            minutes = duration // 60
            seconds = duration % 60
            return f"{minutes}m {seconds}s"
        elif duration < 86400:
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            return f"{hours}h {minutes}m"
        else:
            days = duration // 86400
            hours = (duration % 86400) // 3600
            return f"{days}d {hours}h"

    async def back_logic(self, ctx):
        user_id = ctx.author.id if isinstance(ctx, commands.Context) else ctx.user.id
        if user_id in self.afk_users:
            afk_data = self.afk_users.pop(user_id)
            duration = self.get_afk_duration(afk_data['time'])
            await self.send_response(ctx, f"👋 Welcome back! You were AFK for {duration}")
        else:
            await self.send_response(ctx, "You weren't AFK!")

    @commands.command(name='afklist', help='Show all AFK users and their reasons')
    async def afklist_command(self, ctx):
        embed = discord.Embed(color=discord.Color.from_rgb(43, 45, 49))  # #2B2D31
        embed.set_author(name="AFK List", icon_url=self.bot.user.avatar.url)

        if not self.afk_users:
            embed.add_field(name="No AFK Users", value="Nobody is currently AFK", inline=False)
            await ctx.send(embed=embed)
            return

        # Add fields for each AFK user
        for user_id, data in self.afk_users.items():
            member = ctx.guild.get_member(user_id)
            if member and member.avatar:  # Check if member has an avatar
                duration = self.get_afk_duration(data['time'])
                name = f"{member.display_name}"
                value = (
                    f"Here is {member.mention}'s AFK status.\n"
                    f"**Reason:** {data['reason']}\n"
                    f"**Duration:** {duration}\n"
                    f"**Since:** <t:{data['time']}:R>"
                )
                embed.add_field(name=name, value=value, inline=False)

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.content.startswith((".afk", ".back")):
            return

        # Handle mentions of AFK users
        for mentioned_user in message.mentions:
            if mentioned_user.id in self.afk_users:
                afk_data = self.afk_users[mentioned_user.id]
                timestamp = f"<t:{afk_data['time']}:R>"
                await message.channel.send(
                    f"💤 **{mentioned_user.name}** is AFK: {afk_data['reason']} (since {timestamp})"
                )

        # Handle AFK user returning
        if message.author.id in self.afk_users:
            afk_data = self.afk_users.pop(message.author.id)
            duration = self.get_afk_duration(afk_data['time'])
            await message.channel.send(f"👋 Welcome back **{message.author.name}**! You were AFK for {duration}")

    async def send_response(self, ctx, content):
        if isinstance(ctx, discord.Interaction):
            if ctx.response.is_done():
                await ctx.followup.send(content=content)
            else:
                await ctx.response.send_message(content=content)
        else:
            await ctx.send(content=content)

async def setup(bot):
    await bot.add_cog(AFK(bot))
