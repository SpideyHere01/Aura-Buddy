import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime
from db.mongo import aura_points_collection, admins_collection
import motor
from pymongo import ReturnDocument

class GiveAura(commands.Cog, name="Aura Points Management"):
    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()
        self.LOG_CHANNEL_ID = 1290705365671088211  # Add your actual log channel ID here

    @commands.command(name='giveaura', help="Give aura points to a user")
    async def giveaura_command(self, ctx, member: discord.Member, points: int):
        authorized = await admins_collection.find_one({"user_id": str(ctx.author.id)})
        if not authorized:
            error_embed = discord.Embed(
                description="❌ You are not authorized to use this command.",
                color=discord.Color.from_rgb(255, 85, 85)
            )
            await self.send_response(ctx, embed=error_embed)
            return
        await self.give_aura_logic(ctx, member, points) 

    @app_commands.command(name='giveaura', description="Give aura points to a user")
    async def give_aura_slash(self, interaction: discord.Interaction, member: discord.Member, points: int):
        authorized = await admins_collection.find_one({"user_id": str(interaction.user.id)})
        if not authorized:
            error_embed = discord.Embed(
                description="❌ You are not authorized to use this command.",
                color=discord.Color.from_rgb(255, 85, 85)
            )
            await self.send_response(interaction, embed=error_embed)
            return
        await self.give_aura_logic(interaction, member, points)

    async def give_aura_logic(self, ctx, member: discord.Member, points: int):
        print(f"give_aura_logic called by {ctx.author if isinstance(ctx, commands.Context) else ctx.user}")  # Debug statement
        authorized = await admins_collection.find_one({"user_id": str(ctx.author.id if isinstance(ctx, commands.Context) else ctx.user.id)})
        print(f"Authorized: {authorized is not None}")  # Debug statement
        if not authorized:
            error_embed = discord.Embed(
                description="❌ You are not authorized to use this command.",
                color=discord.Color.from_rgb(255, 85, 85)
            )
            await self.send_response(ctx, embed=error_embed)
            print("Unauthorized user attempted to give aura")  # Debug statement
            return
        print(f"Authorized user. Proceeding to give {points} aura points to {member}")  # Debug statement
        
        if points == 0:
            embed = discord.Embed(
                description="❌ You must award a non-zero number of aura points.",
                color=discord.Color.from_rgb(43, 45, 49)  # #2B2D31
            )
            await self.send_response(ctx, embed=embed)
            return

        user_id = str(member.id)
        user = ctx.author if isinstance(ctx, commands.Context) else ctx.user

        async with self.lock:
            update_result = await aura_points_collection.find_one_and_update(
                {"user_id": user_id},
                {"$inc": {"points": points}},
                return_document=ReturnDocument.AFTER
            )
            new_points = update_result['points'] if update_result else points
            old_points = new_points - points

        # Create success embed
        embed = discord.Embed(
            title="Aura Points Updated",
            description=(
                f"💫 **Points Transfer**\n"
                f"Recipient: {member.mention}\n"
                f"Amount: `{points:,}` points\n"
                f"New Balance: `{new_points:,}` points"
            ),
            color=discord.Color.from_rgb(43, 45, 49)  # #2B2D31
        )
        
        embed.set_author(name=f"Awarded by {user.display_name}", icon_url=user.display_avatar.url)
        embed.set_footer(text=f"Previous Balance: {old_points:,} points")
        
        await self.send_response(ctx, embed=embed)

        # Log the transaction
        log_embed = discord.Embed(
            title="Aura Points Transfer Log",
            description=(
                f"👤 **Moderator:** {user.mention}\n"
                f"👥 **Recipient:** {member.mention}\n"
                f"💫 **Amount:** `{points:,}` points\n"
                f"📊 **New Balance:** `{new_points:,}` points"
            ),
            color=discord.Color.from_rgb(43, 45, 49)  # #2B2D31
        )
        log_embed.timestamp = datetime.now()
        
        log_channel = self.bot.get_channel(self.LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=log_embed)

        self.bot.dispatch('aura_points_updated', member)

    def save_aura_points(self):
        # Removed: Use MongoDB instead
        pass

    async def send_response(self, ctx, content=None, embed=None):
        if isinstance(ctx, discord.Interaction):
            await ctx.response.send_message(content=content, embed=embed)
        else:
            await ctx.send(content=content, embed=embed)

async def setup(bot):
    await bot.add_cog(GiveAura(bot))