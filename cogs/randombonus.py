import discord
from discord.ext import commands
import random
from datetime import datetime, timedelta
from db.mongo import aura_points_collection, last_used_collection

class RandomBonus(commands.Cog, name="Random Bonus"):
    def __init__(self, bot):
        self.bot = bot
        self.LOG_CHANNEL_ID = 1290705365671088211  # Add your actual log channel ID here

    async def randombonus_logic(self, ctx):
        current_time = datetime.utcnow()
        user_id = str(ctx.author.id if isinstance(ctx, commands.Context) else ctx.user.id)
        user = ctx.author if isinstance(ctx, commands.Context) else ctx.user

        last_used_doc = await last_used_collection.find_one({"user_id": user_id})
        if last_used_doc:
            last_time = last_used_doc['last_used']
            time_difference = current_time - last_time
            if time_difference < timedelta(hours=3):
                remaining_time = timedelta(hours=3) - time_difference
                hours, remainder = divmod(int(remaining_time.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                
                embed = discord.Embed(
                    description=f"⏰ You need to wait **{hours}h {minutes}m {seconds}s** before claiming again.",
                    color=discord.Color.from_rgb(43, 45, 49)  # #2B2D31
                )
                await self.send_response(ctx, embed=embed)
                return

        # Calculate bonus points with rarity system
        rarity_roll = random.random()  # Returns a number between 0 and 1
        
        if rarity_roll < 0.05:  # 5% chance for epic reward
            bonus = random.randint(200, 500)
            rarity_text = "🌟 **EPIC BONUS!**"
        else:  # 95% chance for normal reward
            bonus = random.randint(10, 50)
            rarity_text = "💫 **Bonus Reward**"

        user_doc = await aura_points_collection.find_one({"user_id": user_id})
        new_total = (user_doc['points'] if user_doc else 0) + bonus

        # Create success embed
        embed = discord.Embed(
            title="Random Bonus Claimed",
            description=(
                f"{rarity_text}\n"
                f"Amount: `{bonus:,}` points\n"
                f"New Balance: `{new_total:,}` points"
            ),
            color=discord.Color.from_rgb(43, 45, 49)  # #2B2D31
        )
        
        embed.set_author(name=f"{user.display_name}'s Random Bonus", icon_url=user.display_avatar.url)
        embed.set_footer(text="Try again in 3 hours!")

        await self.send_response(ctx, embed=embed)

        # Log the event
        log_embed = discord.Embed(
            title="Random Bonus Log",
            description=(
                f"👤 **User:** {user.mention}\n"
                f"💫 **Bonus:** `{bonus:,}` points\n"
                f"📊 **New Balance:** `{new_total:,}` points"
            ),
            color=discord.Color.from_rgb(43, 45, 49)  # #2B2D31
        )
        log_embed.timestamp = current_time
        
        log_channel = self.bot.get_channel(self.LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=log_embed)

        # Update aura points
        await aura_points_collection.update_one(
            {"user_id": user_id},
            {"$set": {"points": new_total}},
            upsert=True
        )

        # Update last used
        await last_used_collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_used": current_time}},
            upsert=True
        )

    def save_aura_points(self):
        # Removed: Use MongoDB instead
        pass

    def save_last_used(self):
        # Removed: Use MongoDB instead
        pass

    async def send_response(self, ctx, content=None, embed=None):
        if isinstance(ctx, discord.Interaction):
            await ctx.response.send_message(content=content, embed=embed)
        else:
            await ctx.send(content=content, embed=embed)

    @commands.group(name='random', aliases=['r'], help="Random commands group")
    async def random(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Please use a subcommand. Available subcommand: `bonus`")

    @random.command(name='bonus', aliases=['b'], help="Get random bonus aura points")
    async def bonus(self, ctx):
        await self.randombonus_logic(ctx)

    @commands.command(name='random bonus', description="Get random bonus aura points")
    async def randombonus_slash(self, interaction: discord.Interaction):
        await self.randombonus_logic(interaction)

async def setup(bot):
    await bot.add_cog(RandomBonus(bot))
