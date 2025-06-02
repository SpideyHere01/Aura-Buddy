import discord
from discord.ext import commands
from discord import app_commands
import os
import json
import datetime
from typing import Optional
from db.mongo import aura_points_collection

class Profile(commands.Cog, name="Profile Management"):
    def __init__(self, bot):
        self.bot = bot
        self.last_reload = 0

    @commands.command(name='profile')
    async def profile_command(self, ctx, member: discord.Member = None):
        await self.profile_logic(ctx, member)
    
    @app_commands.command(name='profile', description="View your or another user's profile")
    async def profile_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        await self.profile_logic(interaction, member)

    async def profile_logic(self, ctx, member: Optional[discord.Member] = None):
        try:
            member = member or (ctx.author if isinstance(ctx, commands.Context) else ctx.user)
            user_id = str(member.id)
            data = await aura_points_collection.find_one({'user_id': user_id})  # Add await here
            points = data['points'] if data else 0

            # Create embed
            embed_color = 0x2b2d31
            embed = discord.Embed(title=f"{member.display_name}'s Profile", color=embed_color)

            # Set thumbnail to user's avatar
            embed.set_thumbnail(url=member.display_avatar.url)

            # Add general info
            embed.add_field(name="Username", value=f"{member}", inline=True)
            embed.add_field(name="User ID\u2800\u2800", value=member.id, inline=True)  # Added invisible spacing
            embed.add_field(name="Status", value=str(member.status).title(), inline=True)

            # Dates
            embed.add_field(name="Joined Server", value=member.joined_at.strftime('%Y-%m-%d'), inline=True)
            embed.add_field(name="Account Created", value=member.created_at.strftime('%Y-%m-%d'), inline=True)

            # Aura Points
            embed.add_field(name="Aura Points", value=f"```{points:,}```", inline=True)

            # Handle roles
            roles = sorted([role for role in member.roles[1:]], key=lambda x: x.position, reverse=True)
            role_mentions = [f"{role.mention}\u2800" for role in roles] 
            if role_mentions:
                roles_field = ''.join(role_mentions)
                embed.add_field(name="Roles", value=roles_field, inline=False)
            else:
                embed.add_field(name="Roles", value="No roles", inline=False)

            # Badges
            badges = []
            flags = member.public_flags

            # Badge mapping with emojis (update with your own custom emojis)
            badge_emojis = {
                "staff": "<:staff_badge:123456789012345678>",
                "partner": "<:partner_badge:123456789012345678>",
                "hypesquad": "<:hypesquad_badge:123456789012345678>",
                # Add more mappings as needed
            }

            for badge_name, emoji in badge_emojis.items():
                if getattr(flags, badge_name, False):
                    badges.append(emoji)

            if badges:
                badges_field = ' '.join(badges)
                embed.add_field(name="Badges", value=badges_field, inline=False)

            await self.send_response(ctx, embed=embed)

        except Exception as e:
            # Log the exception and inform the user
            print(f"Error in profile command: {type(e).__name__}: {str(e)}")
            error_embed = discord.Embed(
                description="⚠️ Unable to display the profile at this time.",
                color=discord.Color.from_rgb(43, 45, 49)
            )
            await self.send_response(ctx, embed=error_embed)

    async def send_response(self, ctx, **kwargs):
        try:
            if isinstance(ctx, discord.Interaction):
                await ctx.response.send_message(**kwargs)
            else:
                await ctx.send(**kwargs)
        except Exception as e:
            # Log any exceptions during sending the response
            print(f"Error in send_response: {type(e).__name__}: {str(e)}")

async def setup(bot):
    await bot.add_cog(Profile(bot))
