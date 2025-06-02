import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import os

class Feedback(commands.Cog, name="Feedback"):
    def __init__(self, bot):
        self.bot = bot
        self.last_feedback_used = {}
        self.FEEDBACK_CHANNEL_ID = 1290705957600362538  # Update with your actual channel ID

    @commands.command(name='feedback', help="Give feedback to improve the server")
    async def feedback_command(self, ctx, *, feedback_message):
        await self.feedback_logic(ctx, feedback_message)

    @app_commands.command(name='feedback', description="Give feedback to improve the server")
    async def feedback_slash(self, interaction: discord.Interaction, feedback_message: str):
        await self.feedback_logic(interaction, feedback_message)

    async def feedback_logic(self, ctx, feedback_message):
        current_time = datetime.now()
        user_id = ctx.author.id if isinstance(ctx, commands.Context) else ctx.user.id
        user = ctx.author if isinstance(ctx, commands.Context) else ctx.user

        # Check cooldown
        if user_id in self.last_feedback_used:
            last_time = self.last_feedback_used[user_id]
            time_difference = current_time - last_time

            if time_difference < timedelta(hours=24):
                remaining_time = timedelta(hours=24) - time_difference
                hours, remainder = divmod(int(remaining_time.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                
                embed = discord.Embed(
                    description=f"⏰ You need to wait **{hours}h {minutes}m {seconds}s** before sending feedback again.",
                    color=discord.Color.from_rgb(43, 45, 49)  # #2B2D31
                )
                await self.send_response(ctx, embed=embed)
                return

        # Send feedback to the designated channel
        feedback_channel = self.bot.get_channel(self.FEEDBACK_CHANNEL_ID)
        if feedback_channel:
            feedback_embed = discord.Embed(
                title="New Feedback Received",
                description=feedback_message,
                color=discord.Color.from_rgb(43, 45, 49)  # #2B2D31
            )
            feedback_embed.set_author(name=f"Feedback from {user.display_name}", icon_url=user.display_avatar.url)
            feedback_embed.set_footer(text=f"User ID: {user_id}")
            feedback_embed.timestamp = current_time
            
            await feedback_channel.send(embed=feedback_embed)

        # Send confirmation to user
        confirm_embed = discord.Embed(
            title="Feedback Submitted",
            description=(
                "💫 **Thank you for your feedback!**\n\n"
                "Your message has been sent to the staff team.\n"
                "We appreciate your contribution to improving the bot."
            ),
            color=discord.Color.from_rgb(43, 45, 49)  # #2B2D31
        )
        confirm_embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        confirm_embed.set_footer(text="You can submit another feedback in 24 hours")
        
        await self.send_response(ctx, embed=confirm_embed)

        # Update cooldown
        self.last_feedback_used[user_id] = current_time

    async def send_response(self, ctx, content=None, embed=None):
        if isinstance(ctx, discord.Interaction):
            await ctx.response.send_message(content=content, embed=embed)
        else:
            await ctx.send(content=content, embed=embed)

async def setup(bot):
    await bot.add_cog(Feedback(bot))