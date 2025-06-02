import discord
from discord.ext import commands
from discord import app_commands
import os
import json
from typing import Union, List, Tuple, Optional
from discord.ext import commands, tasks
from db.mongo import aura_points_collection

class LeaderboardView(discord.ui.View):
    def __init__(self, cog, ctx, leaderboard_type="server", page=0):
        super().__init__(timeout=60)
        self.cog = cog
        self.ctx = ctx
        self.leaderboard_type = leaderboard_type
        self.page = page
        self.user = ctx.author if isinstance(ctx, commands.Context) else ctx.user
        self.total_users = 0  # Initialize total_users
        self.update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message("Only the user who ran this command can use these buttons!", ephemeral=True)
            return False
        return True

    def update_buttons(self):
        self.global_button.style = discord.ButtonStyle.primary if self.leaderboard_type == "global" else discord.ButtonStyle.secondary
        self.server_button.style = discord.ButtonStyle.primary if self.leaderboard_type == "server" else discord.ButtonStyle.secondary
        
        # Disable navigation buttons for global leaderboard
        if self.leaderboard_type == "global":
            self.previous_page.disabled = True
            self.next_page.disabled = True
        else:
            # Only enable navigation for server leaderboard
            self.previous_page.disabled = self.page == 0
            total_users = self.total_users
            self.next_page.disabled = (self.page + 1) * 5 >= total_users

    @discord.ui.button(label="🌍 Global", style=discord.ButtonStyle.secondary, custom_id="global_lb")
    async def global_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.leaderboard_type = "global"
        self.page = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=await self.cog.get_leaderboard_embed(self.ctx, self.leaderboard_type, self.page), view=self)

    @discord.ui.button(label="🏠 Server", style=discord.ButtonStyle.secondary, custom_id="server_lb")
    async def server_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.leaderboard_type = "server"
        self.page = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=await self.cog.get_leaderboard_embed(self.ctx, self.leaderboard_type, self.page), view=self)

    @discord.ui.button(label="⬅️ Previous", style=discord.ButtonStyle.secondary, custom_id="previous")
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(0, self.page - 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=await self.cog.get_leaderboard_embed(self.ctx, self.leaderboard_type, self.page), view=self)

    @discord.ui.button(label="Next ➡️", style=discord.ButtonStyle.secondary, custom_id="next")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=await self.cog.get_leaderboard_embed(self.ctx, self.leaderboard_type, self.page), view=self)

class Leaderboard(commands.Cog, name="Aura Management"):
    """A cog to handle the aura points leaderboard system."""
    
    def __init__(self, bot):
        self.bot = bot
        self.aura_points = {}
        self.user_cache = {}
        self.refresh_leaderboard.start()

    def cog_unload(self):
        self.refresh_leaderboard.cancel()

    @tasks.loop(minutes=5)
    async def refresh_leaderboard(self):
        """Refresh the leaderboard data periodically."""
        pass

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command(name='leaderboard', aliases=['lb'])
    async def leaderboard_command(self, ctx):
        """Display the server aura points leaderboard."""
        await self.leaderboard_logic(ctx, "server")

    @commands.command(name='lb_global', help="Display the global aura points leaderboard")
    async def global_leaderboard_command(self, ctx):
        await self.leaderboard_logic(ctx, "global")

    @app_commands.command(name='leaderboard', description="Display the aura points leaderboard")
    @app_commands.choices(leaderboard_type=[
        app_commands.Choice(name="Server", value="server"),
        app_commands.Choice(name="Global", value="global")
    ])
    async def leaderboard_slash(self, interaction: discord.Interaction, leaderboard_type: str = "server"):
        await self.leaderboard_logic(interaction, leaderboard_type)

    async def leaderboard_logic(self, ctx, leaderboard_type):
        print(f"{leaderboard_type.capitalize()} Leaderboard command invoked")

        # Fetch total users asynchronously
        if leaderboard_type == "server":
            users = await self.get_server_leaderboard(ctx.guild)
        else:
            users = await self.get_global_leaderboard()
        total_users = len(users)

        view = LeaderboardView(self, ctx, leaderboard_type)
        view.total_users = total_users  # Set total_users in the view
        embed = await self.get_leaderboard_embed(ctx, leaderboard_type, 0)
        
        if isinstance(ctx, discord.Interaction):
            await ctx.response.send_message(embed=embed, view=view)
        else:
            await ctx.send(embed=embed, view=view)

    async def get_leaderboard_embed(self, ctx, leaderboard_type, page):
        if leaderboard_type == "server":
            title = "🏆 Server Aura Points Leaderboard"
            users = await self.get_server_leaderboard(ctx.guild)
            gif_url = "https://media.giphy.com/media/3o6fJ0mUt4WWF1Z0kw/giphy.gif"
        else:
            title = "🌍 Global Aura Points Leaderboard"
            users = await self.get_global_leaderboard()
            gif_url = "https://media.giphy.com/media/3o7aCWJavAgtBzLWrS/giphy.gif"

        start_top = page * 5
        end_top = start_top + 5
        top_users = users[start_top:end_top]

        total_users = len(users)
        bottom_users = users[-end_top:-start_top] if start_top > 0 else users[-5:]
        
        embed = discord.Embed(title=title)

        # Top users display
        top_leaderboard = f"🏅 **Top Aura Points:**\n"
        for index, (user_id, points) in enumerate(top_users, start=start_top + 1):
            try:
                if leaderboard_type == "server":
                    member = ctx.guild.get_member(int(user_id))
                    user_display = member.mention if member else f"User {user_id}"
                else:
                    user = self.bot.get_user(int(user_id))
                    if user is None:
                        user = await self.bot.fetch_user(int(user_id))
                    user_display = user.name if user else f"User {user_id}"
            except Exception as e:
                print(f"Error fetching user {user_id}: {e}")
                user_display = f"User {user_id}"
            
            line = f"{index}. {user_display}: **{points:,}** points\n"
            top_leaderboard += line

        embed.add_field(name="", value=top_leaderboard, inline=False)

        # Bottom users display
        if bottom_users:
            bottom_leaderboard = f"💨 **Bottom Aura Points:**\n"
            # Sort bottom users by points in ascending order (lowest first)
            bottom_users = sorted(bottom_users, key=lambda x: x[1])
            
            # Calculate starting position based on page number
            start_position = (page * 5) + 1
            
            for i, (user_id, points) in enumerate(bottom_users):
                try:
                    if leaderboard_type == "server":
                        member = ctx.guild.get_member(int(user_id))
                        user_display = member.mention if member else f"User {user_id}"
                    else:
                        user = self.bot.get_user(int(user_id))
                        if user is None:
                            user = await self.bot.fetch_user(int(user_id))
                        user_display = user.name if user else f"User {user_id}"
                except Exception as e:
                    print(f"Error fetching user {user_id}: {e}")
                    user_display = f"User {user_id}"
                
                position = start_position + i
                line = f"{position}. {user_display}: **{points:,}** points\n"
                bottom_leaderboard += line

            embed.add_field(name="", value=bottom_leaderboard, inline=False)

        embed.set_thumbnail(url=gif_url)
        
        if leaderboard_type == "server":
            total_pages = (len(users) + 4) // 5
            footer_text = f"Page {page + 1}/{total_pages} | Server: {ctx.guild.name}"
            embed.set_footer(text=footer_text)
        else:
            embed.set_footer(text="Global Leaderboard")

        return embed

    async def get_server_leaderboard(self, guild):
        # Fetch all users with aura points
        all_users_cursor = aura_points_collection.find().sort("points", -1)
        all_users = await all_users_cursor.to_list(length=None)

        # Get a set of member IDs in the guild for faster lookup
        guild_member_ids = set(member.id for member in guild.members)

        # Filter users to those who are members of the guild
        server_users = [
            (user_data['user_id'], user_data['points'])
            for user_data in all_users
            if int(user_data['user_id']) in guild_member_ids
        ]

        # Sort the list by points in descending order
        server_users.sort(key=lambda x: x[1], reverse=True)

        return server_users

    async def get_global_leaderboard(self):
        global_points_cursor = aura_points_collection.find().sort("points", -1)
        global_points = await global_points_cursor.to_list(length=None)
        return [(user_data['user_id'], user_data['points']) for user_data in global_points]

    def get_medal(self, position):
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        return medals.get(position, "🏅")

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))