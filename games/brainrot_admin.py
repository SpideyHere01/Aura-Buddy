import discord
from discord.ext import commands
import json
import os   
import logging
from datetime import datetime
from typing import List, Optional

class BrainrotAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('brainrot_admin')
        self.admin_users = self.load_admin_users()
        self.logger.info(f"BrainrotAdmin initialized with admins: {self.admin_users}")

    def load_admin_users(self) -> List[str]:
        try:
            with open('authorized_users.json', 'r') as f:
                data = json.load(f)
                return data.get('authorized_user_ids', [])
        except Exception as e:
            self.logger.error(f"Error loading authorized users: {e}")
            return []

    async def cog_check(self, ctx):
        user_id = str(ctx.author.id)
        self.logger.debug(f"Admin command attempt by {ctx.author} ({user_id})")
        self.logger.debug(f"Admin list: {self.admin_users}")
        
        is_admin = user_id in self.admin_users
        return is_admin

    def load_user_data(self):
        try:
            os.makedirs('data', exist_okay=True)
            file_path = 'data/users.json'
            
            if not os.path.exists(file_path):
                default_data = {"users": {}}
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, indent=2)
                return default_data
                
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading user data: {e}")
            return {"users": {}}

    def save_user_data(self, data):
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/users.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.info("User data successfully saved.")
            return True
        except Exception as e:
            self.logger.error(f"Error saving user data: {e}")
            return False

    @commands.command(name="adminreset")
    async def reset_all(self, ctx):
        try:
            data = {"users": {}}
            if self.save_user_data(data):
                await self.send_success(ctx, "Successfully reset all user data!", "All user data has been reset.")
            else:
                await self.send_error(ctx, "Error occurred while resetting data!", "An error occurred while processing the command.")
        except Exception as e:
            self.logger.error(f"Error in reset_all: {e}")
            await self.send_error(ctx, "An error occurred while processing the command!", "An error occurred while processing the command.")

    @commands.command(name="resetuser")
    async def reset_user(self, ctx, user_id: str):
        try:
            data = self.load_user_data()
            if user_id in data["users"]:
                data["users"][user_id] = {
                    "last_claim": None,
                    "claimed_characters": []
                }
                if self.save_user_data(data):
                    await self.send_success(ctx, f"Successfully reset data for user {user_id}", "Data reset for user " + user_id)
                else:
                    await self.send_error(ctx, "Error occurred while saving data!", "An error occurred while saving data.")
            else:
                await self.send_error(ctx, "User not found in database!", "Attempted to reset non-existent user " + user_id)
        except Exception as e:
            self.logger.error(f"Error in reset_user: {e}")
            await self.send_error(ctx, "An error occurred while processing the command!", "An error occurred while processing the command.")

    @commands.command(name="dropstats")
    async def view_stats(self, ctx):
        try:
            data = self.load_user_data()
            total_users = len(data["users"])
            total_claims = sum(len(u["claimed_characters"]) for u in data["users"].values())
            
            embed = discord.Embed(
                title="📊 Brainrot Drop Statistics",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Overview",
                value=f"```• Total Users: {total_users:,}\n• Total Claims: {total_claims:,}```",
                inline=False
            )
            
            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Error in view_stats: {e}")
            await self.send_error(ctx, "An error occurred while retrieving statistics!", "An error occurred while retrieving statistics.")

    @commands.command(name="refreshadmin")
    async def refresh_admins(self, ctx):
        try:
            self.admin_users = self.load_admin_users()
            await self.send_success(ctx, "Admin users list refreshed!", "Admin users list has been refreshed.")
        except Exception as e:
            self.logger.error(f"Error refreshing admin users: {e}")
            await self.send_error(ctx, "An error occurred while refreshing admin users!", "An error occurred while refreshing admin users.")

    @commands.command(name="clearcooldown")
    @commands.has_permissions(administrator=True)
    async def clear_cooldown(self, ctx, user: discord.User):
        try:
            with open('data/users.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            user_id = str(user.id)
            if user_id in data["users"]:
                data["users"][user_id]["last_claim"] = None
                with open('data/users.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                await ctx.send(f"Cooldown cleared for {user.mention}.")
            else:
                await ctx.send(f"User {user.mention} not found in the database.")
        except Exception as e:
            self.logger.error(f"Error clearing cooldown for user {user.id}: {e}")
            await self.send_error(ctx, "An error occurred while clearing the cooldown!", "An error occurred while clearing the cooldown.")

    @commands.command(name="backupdata")
    async def backup(self, ctx):
        try:
            data = self.load_user_data()
            backup_path = f'data/backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            await ctx.send(f"✅ Backup created: `{backup_path}`")
            self.logger.info(f"Backup created at {backup_path}")
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            await self.send_error(ctx, "An error occurred while creating backup!", "An error occurred while creating backup.")

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.BotMissingPermissions):
            missing_perms = '\n'.join([f'• {perm.replace("_", " ").title()}' for perm in error.missing_permissions])
            await ctx.send(f"❌ I need the following permissions to work properly:\n{missing_perms}")

        elif isinstance(error, commands.MissingPermissions):
            missing_perms = '\n'.join([f'• {perm.replace("_", " ").title()}' for perm in error.missing_permissions])
            await ctx.send(f"❌ You need the following permissions:\n{missing_perms}")

        elif isinstance(error, discord.Forbidden):
            if error.code == 60003:
                await ctx.send("❌ 2FA (Two-Factor Authentication) is required for this action.")
            else:
                await ctx.send(f"❌ I don't have permission to perform that action.\nError: {error.text}")

        elif isinstance(error, discord.HTTPException):
            if error.code == 50013:
                await ctx.send("❌ I don't have proper permissions to perform that action.")
            elif error.code == 50007:
                await ctx.send("❌ I cannot send messages to this user. They might have DMs disabled.")
            else:
                await ctx.send(f"❌ An HTTP error occurred: {error.text}")

        elif isinstance(error, commands.CheckFailure):
            await ctx.send("❌ You are not authorized to use these commands.")
            self.logger.warning(f"Access denied for user {ctx.author.name} (ID: {ctx.author.id})")

        else:
            self.logger.error(f"Error in command '{ctx.command}': {error}")
            error_msg = f"❌ An error occurred: {str(error)}"
            if len(error_msg) > 2000:
                error_msg = error_msg[:1997] + "..."
            await ctx.send(error_msg)

    async def send_success(self, ctx, title, description):
        embed = discord.Embed(
            title=f"✅ {title}",
            description=f"```{description}```",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Executed by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    async def send_error(self, ctx, title, description):
        embed = discord.Embed(
            title=f"❌ {title}",
            description=f"```{description}```",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BrainrotAdmin(bot))
