import discord
from discord.ext import commands
import asyncio
from db.mongo import aura_points_collection, admins_collection

class ResetAura(commands.Cog, name="Reset Aura"):
    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()
        self.LOG_CHANNEL_ID = 1290705365671088211  # Add your actual log channel ID here

    @commands.command(name='resetaura')
    async def reset_aura(self, ctx, member: discord.Member = None):
        authorized = await admins_collection.find_one({"user_id": str(ctx.author.id)})
        if not authorized:
            error_embed = discord.Embed(
                description="❌ You are not authorized to use this command.",
                color=discord.Color.from_rgb(255, 85, 85)
            )
            await ctx.send(embed=error_embed)
            print("Unauthorized user attempted to reset aura")  # Debug statement
            return

        member = member or ctx.author
        user_id = str(member.id)

        async with self.lock:
            user_doc = await aura_points_collection.find_one({"user_id": user_id})
            if user_doc:
                old_points = user_doc['points']
                await aura_points_collection.update_one({"user_id": user_id}, {"$set": {"points": 0}})
                await ctx.send(f"{member.mention}'s aura points have been reset from {old_points} to 0.")
                await self.log_event(ctx, f"{member.mention}'s aura points were reset from {old_points} to 0 by {ctx.author.mention}.")
            else:
                await ctx.send(f"{member.mention} does not have any aura points to reset.")

        # Dispatch an event to notify other cogs

        # Dispatch an event to notify other cogs
        self.bot.dispatch('aura_points_updated', member)

    def save_aura_points(self):
        # Removed: Use MongoDB instead
        pass

    async def log_event(self, ctx, message):
        log_channel = self.bot.get_channel(1290705365671088211)  # Update with your actual log channel ID
        if log_channel:
            await log_channel.send(message)

async def setup(bot):
    await bot.add_cog(ResetAura(bot))
