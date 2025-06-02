import discord
from discord.ext import commands
from discord import app_commands
import random

class Tharki(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='tharki', help="Check the tharki level of a user")
    async def tharki_command(self, ctx, user: discord.Member = None):
        await self.tharki_logic(ctx, user)

    @app_commands.command(name='tharki', description="Check the tharki level of a user")
    async def tharki_slash(self, interaction: discord.Interaction, user: discord.Member = None):
        await self.tharki_logic(interaction, user)

    async def tharki_logic(self, ctx, user: discord.Member = None):
        user = user or (ctx.author if isinstance(ctx, commands.Context) else ctx.user)
        tharki_level = random.randint(0, 100)
        
        # Create progress bar
        progress = "█" * (tharki_level // 10) + "░" * ((100 - tharki_level) // 10)
        
        # Get emoji based on tharki level
        if tharki_level < 20:
            emoji = "😇"
        elif tharki_level < 40:
            emoji = "😏"
        elif tharki_level < 60:
            emoji = "😈"
        elif tharki_level < 80:
            emoji = "🥵"
        else:
            emoji = "🔥"

        reasons = [
            "Bro, apni jaan pe thoda control karo.",
            "10 selfies like kiye ek saath! Tharki alert.",
            "It's okay, thoda chill maaro.",
            "Stop stalking Instagram pe!",
            "DMs mein slide karne ka master!",
            "Har story pe first comment karta hai ye banda.",
            "Professional heart reactor spotted!",
            "Sabki profile picture save karta hai ye.",
        ]
        reason = random.choice(reasons)

        embed = discord.Embed(
            title=f"Tharki Meter {emoji}",
        )
        embed.add_field(
            name=f"Level: {tharki_level}%",
            value=f"```{progress}```",
            inline=False
        )
        embed.add_field(
            name="Reason",
            value=reason,
            inline=False
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Requested for {user.display_name}")
        
        if isinstance(ctx, discord.Interaction):
            await ctx.response.send_message(embed=embed)
        else:
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Tharki(bot))