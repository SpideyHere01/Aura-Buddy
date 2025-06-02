import discord
from discord import app_commands
import random
from discord.ext import commands

class Ship(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.love_emojis = ["💖", "💝", "💓", "💗", "💕", "❤️", "💘", "💞"]
        self.ship_responses = {
            "perfect": [
                "Ekdum made for each other! Shaadi when? 👰🤵",
                "Rab ne bana di jodi! 🎵",
                "Perfect match! Invitation card ready karo! 💌",
                "100% compatible! Time to meet the parents! 👨‍👩‍👧‍👦"
            ],
            "strong": [
                "Kuch toh hai! Give it a shot! ✨",
                "Bohot scope hai! Go for it! 🌟",
                "Strong vibes! Something special brewing! ☕",
                "Destiny has plans for you two! 🎯"
            ],
            "moderate": [
                "50-50 chance hai, try karlo. 🎲",
                "Potential hai, thoda effort lagao! 💪",
                "Not bad, not bad at all! 👀",
                "Kuch toh chemistry hai! 🧪"
            ],
            "low": [
                "Mushkil hai bhai, but impossible nahi. 🤔",
                "Thoda tough hai, but who knows! 🍀",
                "Universe is testing your patience! 😅",
                "Uphill battle, but miracles happen! 🙏"
            ],
            "friends": [
                "Dosti me hi khush raho dono. 🤝",
                "Best friends forever material! 🫂",
                "Friendship goals > Relationship goals 🎯",
                "Yaari > Pyaari 🤗"
            ]
        }

    def get_random_member(self, guild):
        return random.choice([member for member in guild.members if not member.bot])

    def generate_ship_name(self, name1, name2):
        # Generate two ship names by combining parts of both names
        ship_name1 = name1[:len(name1)//2] + name2[len(name2)//2:]
        ship_name2 = name2[:len(name2)//2] + name1[len(name1)//2:]
        return f"{ship_name1} / {ship_name2}"

    @commands.command(name='ship', help="Check the love compatibility with a random server member or specified user")
    async def ship_command(self, ctx, user: discord.Member = None):
        if user is None:
            user1 = ctx.author
            user2 = self.get_random_member(ctx.guild)
        else:
            user1 = ctx.author
            user2 = user
        await self.ship_logic(ctx, user1, user2)

    @app_commands.command(name='ship', description="Check the love compatibility with a random server member or specified user")
    async def ship_slash(self, interaction: discord.Interaction, user: discord.Member = None):
        if user is None:
            user1 = interaction.user
            user2 = self.get_random_member(interaction.guild)
        else:
            user1 = interaction.user
            user2 = user
        await self.ship_logic(interaction, user1, user2)

    async def ship_logic(self, ctx, user1, user2):
        ship_level = random.randint(0, 100)
        
        # Create embed with dark theme color
        embed = discord.Embed(color=discord.Color.from_rgb(43, 45, 49))  # Discord dark theme color
        
        embed.set_author(
            name="Love Calculator",
            icon_url=self.bot.user.avatar.url
        )
        
        # Only show one avatar as thumbnail
        if user2.avatar:
            embed.set_thumbnail(url=user2.avatar.url)

        # Determine the status message and get random response
        if ship_level > 80:
            status = "💖 Perfect Match!"
            message = random.choice(self.ship_responses["perfect"])
        elif ship_level > 60:
            status = "💝 Strong Connection"
            message = random.choice(self.ship_responses["strong"])
        elif ship_level > 40:
            status = "💓 Moderate Chemistry"
            message = random.choice(self.ship_responses["moderate"])
        elif ship_level > 20:
            status = "💔 Low Compatibility"
            message = random.choice(self.ship_responses["low"])
        else:
            status = "💔 Low Compatibility"
            message = random.choice(self.ship_responses["friends"])

        # Generate combined love names
        ship_name = self.generate_ship_name(user1.name, user2.name)

        embed.add_field(
            name=status,
            value=f"**Shipping:** {user1.mention} {random.choice(self.love_emojis)} {user2.mention}\n"
                  f"**Ship Names:** {ship_name}\n"
                  f"**Compatibility:** {ship_level}%\n"
                  f"**Status:** {message}",
            inline=False
        )

        # Create a simple progress bar using blocks
        progress_length = 10
        filled = int((ship_level / 100) * progress_length)
        empty = progress_length - filled
        
        # Using Unicode blocks for a clean look
        bar = "█" * filled + "▒" * empty

        embed.add_field(
            name="Love Meter",
            value=f"{bar} {ship_level}%",
            inline=False
        )

        if isinstance(ctx, discord.Interaction):
            await ctx.response.send_message(embed=embed)
        else:
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Ship(bot))