import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import json
from db.mongo import aura_points_collection, authorized_users_collection

class TradeAura(commands.Cog, name="Trade Aura"):
    def __init__(self, bot):
        self.bot = bot
        self.aura_points = {}
        self.LOG_CHANNEL_ID = 1290705365671088211  # Add your actual log channel ID here

    @commands.command(name='tradeaura', help="Trade aura points with another user", aliases=['ta'])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def tradeaura_command(self, ctx, member: discord.Member = None, points: int = None):
        if member is None:
            error_embed = discord.Embed(
                description="❌ Please mention the user you want to trade aura points with.",
                color=discord.Color.from_rgb(255, 85, 85)
            )
            await ctx.send(embed=error_embed)
            return
        if points is None:
            error_embed = discord.Embed(
                description="❌ Please specify the number of aura points you want to trade.",
                color=discord.Color.from_rgb(255, 85, 85)
            )
            await ctx.send(embed=error_embed)
            return
        await self.tradeaura_logic(ctx, member, points)

    @app_commands.command(name='tradeaura', description="Trade aura points with another user")
    @app_commands.checks.cooldown(1, 30)
    async def tradeaura_slash(self, interaction: discord.Interaction, member: discord.Member, points: int):
        await self.tradeaura_logic(interaction, member, points)

    @commands.group(name='trade')
    async def trade(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Use `.trade aura <user> <amount>` or `.ta <@user> <amount>` ")

    @trade.command(name='aura')
    async def trade_aura(self, ctx, member: discord.Member = None, points: int = None):
        if member is None:
            error_embed = discord.Embed(
                description="❌ Please mention the user you want to trade aura points with.",
                color=discord.Color.from_rgb(255, 85, 85)
            )
            await ctx.send(embed=error_embed)
            return
        if points is None:
            error_embed = discord.Embed(
                description="❌ Please specify the number of aura points you want to trade.",
                color=discord.Color.from_rgb(255, 85, 85)
            )
            await ctx.send(embed=error_embed)
            return
        await self.tradeaura_logic(ctx, member, points)

    async def tradeaura_logic(self, ctx, member: discord.Member, points: int):
        if member.bot:
            error_embed = discord.Embed(
                description="❌ You cannot trade aura points with bots.",
                color=discord.Color.from_rgb(43, 45, 49)
            )
            await self.send_response(ctx, embed=error_embed)
            return
        
        try:
            points = int(points)
        except ValueError:
            error_embed = discord.Embed(
                description="❌ Points must be a valid number.",
                color=discord.Color.from_rgb(43, 45, 49)
            )
            await self.send_response(ctx, embed=error_embed)
            return
        
        if points <= 0:
            error_embed = discord.Embed(
                description="❌ You must trade a positive number of aura points.",
                color=discord.Color.from_rgb(43, 45, 49)  # #2B2D31
            )
            await self.send_response(ctx, embed=error_embed)
            return
        
        user_id = str(ctx.author.id if isinstance(ctx, commands.Context) else ctx.user.id)
        member_id = str(member.id)
        user = ctx.author if isinstance(ctx, commands.Context) else ctx.user

        if member.id == user.id:
            error_embed = discord.Embed(
                description="❌ You cannot trade aura points with yourself.",
                color=discord.Color.from_rgb(43, 45, 49)
            )
            await self.send_response(ctx, embed=error_embed)
            return

        user_doc = await aura_points_collection.find_one({"user_id": user_id})
        member_doc = await aura_points_collection.find_one({"user_id": member_id})

        user_aura_points = user_doc['points'] if user_doc else 0
        if user_aura_points < points:
            error_embed = discord.Embed(
                description="❌ You don't have enough aura points to trade.",
                color=discord.Color.from_rgb(43, 45, 49)  # #2B2D31
            )
            await self.send_response(ctx, embed=error_embed)
            return

        if not member_doc:
            await aura_points_collection.insert_one({"user_id": member_id, "points": points})
        else:
            await aura_points_collection.update_one({"user_id": member_id}, {"$inc": {"points": points}})

        await aura_points_collection.update_one({"user_id": user_id}, {"$inc": {"points": -points}})

        confirmation_embed = discord.Embed(
            title="Aura Trade Request",
            description=(
                f"💫 **Trade Details**\n"
                f"**From:** {user.mention}\n"
                f"**To:** {member.mention}\n"
                f"**Amount:** {points} aura points\n\n"
                "Both users must react with ✅ to confirm the trade."
            ),
            color=discord.Color.from_rgb(43, 45, 49)  # #2B2D31
        )
        confirmation_embed.set_author(name=f"Trade Request from {user.display_name}", icon_url=user.display_avatar.url)
        confirmation_embed.set_footer(text="Trade will expire in 60 seconds", icon_url=member.display_avatar.url)

        # Store the original trader's info before the reaction collection
        original_trader = ctx.author if isinstance(ctx, commands.Context) else ctx.user

        confirmation_message = await self.send_response(ctx, embed=confirmation_embed)

        await confirmation_message.add_reaction('✅')
        await confirmation_message.add_reaction('❌')

        def check(reaction, user):
            return (user in [original_trader, member] and 
                    str(reaction.emoji) in ['✅', '❌'] and 
                    reaction.message.id == confirmation_message.id)

        try:
            reactions = []
            participating_users = set()
            while len(reactions) < 2:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                
                if user in participating_users:
                    continue
                
                if str(reaction.emoji) == '❌':
                    cancel_embed = discord.Embed(
                        description=f"❌ Trade has been canceled by {user.display_name}.",
                        color=discord.Color.from_rgb(43, 45, 49)
                    )
                    await confirmation_message.edit(embed=cancel_embed)
                    return
                
                participating_users.add(user)
                reactions.append((reaction, user))

            if all(str(reaction.emoji) == '✅' for reaction, _ in reactions):
                success_embed = discord.Embed(
                    description=f"✅ **{original_trader.display_name}** → **{points}** aura → **{member.display_name}**",
                    color=discord.Color.from_rgb(43, 45, 49)
                )
                await confirmation_message.edit(embed=success_embed)
            else:
                cancel_embed = discord.Embed(
                    description="❌ Trade canceled due to lack of confirmation.",
                    color=discord.Color.from_rgb(43, 45, 49)
                )
                await confirmation_message.edit(embed=cancel_embed)
            
        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                description="⏰ Trade canceled due to timeout. Both users must confirm within 60 seconds.",
                color=discord.Color.from_rgb(43, 45, 49)  # #2B2D31
            )
            await confirmation_message.edit(embed=timeout_embed)

    def save_aura_points(self):
        pass

    async def send_response(self, ctx, content=None, embed=None):
        if isinstance(ctx, discord.Interaction):
            if ctx.response.is_done():
                return await ctx.followup.send(content=content, embed=embed)
        else:
            return await ctx.send(content=content, embed=embed)

async def setup(bot):
    await bot.add_cog(TradeAura(bot))