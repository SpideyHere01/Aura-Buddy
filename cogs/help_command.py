import discord
from discord.ext import commands
from discord import app_commands
import random

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = None
        
        # Updated category definitions with current commands
        self.categories = {
            "Aura Management": {
                "description": "Manage and track aura points",
                "emoji": "✨",
                "gif": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcDI5Y2k4Z3k4bXgweWN1NnBxM2t0bG1xaWR2NXBnOWF1NzVqY2lqbyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3o7aCZDlmQZLe4Q4V2/giphy.gif",
                "commands": {
                    "leaderboard": "View the aura points leaderboard",
                    "aura": "Request aura points for a message",
                    "checkaura": "Check aura points for a user",
                    "tradeaura": "Trade aura points with another user"
                }
            },
            "Daily Activities": {
                "description": "Daily challenges and bonuses",
                "emoji": "📅",
                "gif": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcDd4Y2RxZnBxbWN1ZHd6ZDdwbXE0NXJ5Y2h6ZWx0OWF6ZXBxaXNmaCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3oKIPrc2ngFZ6BTyww/giphy.gif",
                "commands": {
                    "dailyaura": "Complete daily challenge for bonus points",
                    "randombonus": "Get random bonus points"
                }
            },
            "User Interaction": {
                "description": "User profile and status commands",
                "emoji": "👤",
                "gif": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMzk1Y2NiMzBmZDM0ZmM5OGNjNzk4M2JlMzBkN2IyYmZjYTJlNmU2ZiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/LmBsnpDCuturMhtLfw/giphy.gif",
                "commands": {
                    "profile": "View your profile",
                    "av": "View user avatar"
                }
            },
            "Server Interaction": {
                "description": "Server-related commands",
                "emoji": "🏢",
                "gif": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMjM0YzFkYzFkYzM1MmZjOGQ0MzFkM2JlOGJjNmQ5NmYyOGU0MmRlNyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l0HlQXlQ3nHyLMvte/giphy.gif",
                "commands": {
                    "feedback": "Send feedback about the server",
                    "ping": "Check bot latency",
                    "snipe": "View recently deleted messages (1-10)",
                    "editsnipe": "View recently edited messages (1-10)"
                }
            },
            "Fun Commands": {
                "description": "Fun and entertainment commands",
                "emoji": "🎮",
                "gif": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNmZjYzIwYTJiNmY4NzFjMjQzMDEzMzYxOTJiNDQ5Y2JjNjBjMDI0ZCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3o7aCWJavAgtBzLWrS/giphy.gif",
                "commands": {
                    "ship": "Ship two users together",
                    "flirt": "Send a flirty compliment",
                    "roast": "Roast a user",
                    "lafda": "Start a fun fight with someone",
                    "tharki": "Call someone a flirt",
                    "stopwatch": "Start a stopwatch with lap functionality"
                }
            },
            "Shop System": {
                "description": "Aura shop management",
                "emoji": "🛍️",
                "gif": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExOTJjNzM5MzNjYTM1MmNjMmNjMzM1MzM2MzM2MzQzODYzMzYzNjM4MyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3ohhwvOnBaE8AVFHUc/giphy.gif",
                "commands": {
                    "shop": "View the shop",
                    "buy item": "Buy item from shop (`.buy item <name>`)",
                    "add item": "Add item to shop (`.add item <role> <cost>`)",
                    "remove item": "Remove item from shop (`.remove item <name>`)"
                }
            },
            "Server Management": {
                "description": "Server administration commands",
                "emoji": "⚙️",
                "gif": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExYzJlMjQ0YmQzYjM4N2JjMGM4ZDY4ZjQ4MmZkZGNhZWM4ZjY4ZCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3oKIPc9VZj4ylzjcys/giphy.gif",
                "commands": {
                    "enable": "Enable AI or game commands (ai/game)",
                    "disable": "Disable AI or game commands (ai/game)",
                    "status": "Check enabled/disabled modules status"
                }
            },
            "Aura Games": {
                "description": "Card collection and aura games commands",
                "emoji": "🎴",
                "gif": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNmZjYzIwYTJiNmY4NzFjMjQzMDEzMzYxOTJiNDQ5Y2JjNjBjMDI0ZCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3o7aCWJavAgtBzLWrS/giphy.gif",
                "commands": {
                    "drop": "Start a card drop event",
                    "inventory": "View your card collection",
                    "show": "Display a specific card by ID",
                    "sell": "Sell a card for aura points",
                    "sellall": "Sell all non-loser cards",
                    "sellpreview": "Preview potential earnings from selling cards"
                }
            }
        }

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

    @app_commands.command(name="help", description="Shows the help menu")
    async def help_slash(self, interaction: discord.Interaction, category: str = None):
        await self.send_help_embed(interaction, category)

    @commands.command(name="help", aliases=["h"])
    async def help_prefix(self, ctx, category: str = None):
        await self.send_help_embed(ctx, category)

    async def send_help_embed(self, ctx, category: str = None):
        if category:
            category = next((cat for cat in self.categories if cat.lower().replace(self.categories[cat]['emoji'], '').strip() == category.lower()), None)
        
        embed = await self.create_embed(category)
        
        # Get the user ID from either interaction or context
        user_id = ctx.user.id if isinstance(ctx, discord.Interaction) else ctx.author.id
        view = HelpView(self, user_id)

        if isinstance(ctx, discord.Interaction):
            if ctx.response.is_done():
                await ctx.edit_original_response(embed=embed, view=view)
            else:
                await ctx.response.send_message(embed=embed, view=view)
        else:
            message = await ctx.send(embed=embed, view=view)
        
        # Store the message for timeout handling
        view.message = message if not isinstance(ctx, discord.Interaction) else await ctx.original_response()

    async def create_embed(self, category: str = None):
        if category and category in self.categories:
            category_info = self.categories[category]
            embed = discord.Embed(
                title=f"{category_info['emoji']} {category}",
                description=category_info['description'],
                color=discord.Color.from_rgb(43, 45, 49)  # #2B2D31
            )
            for cmd_name, cmd_desc in category_info['commands'].items():
                embed.add_field(name=f"`.{cmd_name}`", value=cmd_desc, inline=True)
            embed.set_thumbnail(url=category_info['gif'])
        else:
            embed = discord.Embed(
                title="🌟 Aura Bot Help Menu",
                description="Select a category below to view its commands.",
                color=discord.Color.from_rgb(43, 45, 49)  # #2B2D31
            )
            for category_name, category_info in self.categories.items():
                embed.add_field(
                    name=f"{category_info['emoji']} {category_name}",
                    value=category_info['description'],
                    inline=True
                )
            embed.set_thumbnail(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcDd4Y2RxZnBxbWN1ZHd6ZDdwbXE0NXJ5Y2h6ZWx0OWF6ZXBxaXNmaCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3oKIPrc2ngFZ6BTyww/giphy.gif")

        embed.set_footer(text="Use /help <category> or .help <category> for more info")
        return embed

class HelpView(discord.ui.View):
    def __init__(self, help_cog, user_id: int):
        super().__init__(timeout=60)
        self.help_cog = help_cog
        self.user_id = user_id
        self.add_category_select()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This menu is not for you!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        # Disable all items in the view when it times out
        for item in self.children:
            item.disabled = True
        # Try to edit the message with disabled components
        try:
            await self.message.edit(view=self)
        except:
            pass

    def add_category_select(self):
        select = discord.ui.Select(
            placeholder="Select a category",
            options=[
                discord.SelectOption(
                    label=category_name.replace(category_info['emoji'], '').strip(),
                    value=category_name,
                    emoji=category_info['emoji'],
                    description=category_info['description'][:100]  # Discord limit
                )
                for category_name, category_info in self.help_cog.categories.items()
            ]
        )
        select.callback = self.select_category_callback
        self.add_item(select)

    async def select_category_callback(self, interaction: discord.Interaction):
        category = interaction.data['values'][0]
        embed = await self.help_cog.create_embed(category)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Random Tip", style=discord.ButtonStyle.primary, emoji="💡")
    async def random_tip(self, interaction: discord.Interaction, button: discord.ui.Button):
        tips = [
            "You can earn bonus aura points by completing daily challenges!",
            "Trade aura points with your friends using the `.tradeaura` command.",
            "Check the leaderboard to see who has the most aura points!",
            "Don't forget to claim your random bonus aura points daily!",
            "Customize your profile using the `.profile` command.",
            "Use the shop to spend your hard-earned aura points!",
            "Set your AFK status when you're away using `.afk`",
            "View someone's avatar in full size with `.av`",
            "Give feedback to help improve the server!",
            "Try out the fun commands like `.flirt` or `.roast` for some laughs!",
            "Use `.masti` to announce someone's broken heart (all in good fun, of course)!",
            "Challenge your friends to a `.friendzone` check and see who's in the danger zone!",
            "Feeling laggy? Use the `.lag` command to pretend you're typing with a delay!"
        ]
        tip = random.choice(tips)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="💡 Random Tip",
                description=tip,
                color=discord.Color.from_rgb(43, 45, 49)  # #2B2D31
            ),
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))