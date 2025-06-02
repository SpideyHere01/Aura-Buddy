import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from db.mongo import aura_points_collection, aura_data_collection

class Dailyaura(commands.Cog, name="Daily Aura"):
    def __init__(self, bot):
        self.bot = bot
        self.LOG_CHANNEL_ID = 1290705365671088211  # Add your actual log channel ID here

    @commands.command(name='dailyaura', help="Claim your daily aura for bonus points")
    async def dailyaura_command(self, ctx):
        await self.dailyaura_logic(ctx)

    @commands.group(name='daily')
    async def daily(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.dailyaura_logic(ctx)

    @daily.command(name='aura')
    async def daily_aura(self, ctx):
        await self.dailyaura_logic(ctx)

    @app_commands.command(name='daily', description="Claim your daily aura for bonus points")
    async def daily_slash(self, interaction: discord.Interaction):
        await self.dailyaura_logic(interaction)

    async def dailyaura_logic(self, ctx):
        current_time = datetime.utcnow()
        user_id = str(ctx.author.id if isinstance(ctx, commands.Context) else ctx.user.id)
        user = ctx.author if isinstance(ctx, commands.Context) else ctx.user

        user_data = await aura_data_collection.find_one({"user_id": user_id})
        if user_data:
            last_claim_time = user_data.get("last_claim_timestamp")
            if last_claim_time:
                last_claim_time = datetime.fromtimestamp(last_claim_time)
                time_difference = current_time - last_claim_time
                if time_difference < timedelta(hours=24):
                    remaining_time = timedelta(hours=24) - time_difference
                    hours, remainder = divmod(int(remaining_time.total_seconds()), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    embed = discord.Embed(
                        description=f"⏰ You need to wait **{hours}h {minutes}m {seconds}s** before claiming again.",
                        color=discord.Color.from_rgb(43, 45, 49)
                    )
                    await self.send_response(ctx, embed=embed)
                    return

        if not user_data:
            user_data = {"user_id": user_id, "streak": 0, "last_claim": None, "last_claim_timestamp": None}

        last_claim_str = user_data.get("last_claim")
        current_date = current_time.strftime("%Y-%m-%d")

        if last_claim_str:
            try:
                last_claim_date = datetime.strptime(last_claim_str, "%Y-%m-%d").date()
                if last_claim_date > current_time.date():
                    last_claim_str = None
                    user_data["last_claim"] = None
            except (ValueError, TypeError):
                last_claim_str = None
                user_data["last_claim"] = None

        if last_claim_str:
            last_claim_date = datetime.strptime(last_claim_str, "%Y-%m-%d").date()
            if last_claim_date == (current_time.date() - timedelta(days=1)):
                user_data["streak"] = user_data.get("streak", 0) + 1
            else:
                user_data["streak"] = 1
        else:
            user_data["streak"] = 1

        user_data["last_claim"] = current_date
        user_data["last_claim_timestamp"] = current_time.timestamp()

        streak_bonus = user_data["streak"] * 10
        base_points = 50
        total_bonus = base_points + streak_bonus

        user_doc = await aura_points_collection.find_one({"user_id": user_id})
        new_total = (user_doc['points'] if user_doc else 0) + total_bonus
        await aura_points_collection.update_one(
            {"user_id": user_id},
            {"$set": {"points": new_total}},
            upsert=True
        )

        await aura_data_collection.update_one(
            {"user_id": user_id},
            {"$set": user_data},
            upsert=True
        )

        # Create success embed
        embed = discord.Embed(
            title="Daily Aura Claimed",
            description=(
                f"💫 **Rewards Breakdown**\n"
                f"Base Reward: `{base_points:,}` points\n"
                f"Streak Bonus: `+{streak_bonus:,}` points\n"
                f"Total Reward: `{total_bonus:,}` points\n\n"
                f"Current Balance: `{new_total:,}` points"
            ),
            color=discord.Color.from_rgb(43, 45, 49)
        )
        
        if user_data['streak'] > 1:
            embed.add_field(
                name="🔥 Current Streak",
                value=f"`{user_data['streak']} days`",
                inline=False
            )
        
        embed.set_author(name=f"{user.display_name}'s Daily Reward", icon_url=user.display_avatar.url)
        embed.set_footer(text="Come back tomorrow for more rewards!")
        
        await self.send_response(ctx, embed=embed)

    def save_aura_data(self):
        # Removed: Use MongoDB instead
        pass

    def save_aura_points(self):
        # Removed: Use MongoDB instead
        pass

    async def send_response(self, ctx, embed):
        if isinstance(ctx, discord.Interaction):
            await ctx.response.send_message(embed=embed)
        else:
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Dailyaura(bot))