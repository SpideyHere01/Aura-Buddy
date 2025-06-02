import discord
from discord.ext import commands
import json
import os
from typing import Dict

class EnableDisable(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = 'servers.json' 
        self.server_settings: Dict[str, Dict[str, bool]] = {}
        self.load_settings()

    def load_settings(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.server_settings = json.load(f)
            else:
                self.server_settings = {}
        except Exception as e:
            print(f"Error loading server settings: {e}")
            self.server_settings = {}

    def save_settings(self):
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.server_settings, f, indent=4)
        except Exception as e:
            print(f"Error saving server settings: {e}")

    def is_module_enabled(self, guild_id: str, module: str) -> bool:
        if guild_id not in self.server_settings:
            return True 
        return self.server_settings[guild_id].get(module, True)

    async def cog_check(self, ctx: commands.Context) -> bool:
        if not ctx.guild:
            return False
        return ctx.author.guild_permissions.administrator

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        if not ctx.guild:
            return
            
        cog = ctx.command.cog
        if not cog:
            return

        cog_path = os.path.dirname(os.path.abspath(cog.__module__))
        is_ai = 'ai' in cog_path
        is_game = 'games' in cog_path

        if not is_ai and not is_game:
            return

        module_type = 'ai' if is_ai else 'game'
        if not self.is_module_enabled(str(ctx.guild.id), module_type):
            await ctx.message.add_reaction('❌')
            await ctx.send(f"{module_type.upper()} commands are disabled on this server.", delete_after=5)
            raise commands.DisabledCommand(f"{module_type.upper()} commands are disabled")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return

        if not self.is_module_enabled(str(message.guild.id), "ai"):
            if message.mentions or "buddy" in message.content.lower():
                return False

    async def bot_check(self, ctx):
        if not ctx.guild:
            return True

        cog = ctx.command.cog
        if not cog:
            return True

        module_path = cog.__module__
        
        # Block game commands
        if 'games.' in module_path and not self.is_module_enabled(str(ctx.guild.id), "game"):
            await ctx.message.add_reaction('❌')
            await ctx.send("Game commands are disabled on this server.", delete_after=5)
            return False
            
        # Block AI commands
        if 'ai.' in module_path and not self.is_module_enabled(str(ctx.guild.id), "ai"):
            await ctx.message.add_reaction('❌')
            await ctx.send("AI commands are disabled on this server.", delete_after=5)
            return False

        return True

    @commands.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def disable_module(self, ctx: commands.Context, module: str):
        if module.lower() not in ['ai', 'game']:
            await ctx.send("Invalid module. Use 'ai' or 'game'.")
            return

        guild_id = str(ctx.guild.id)
        if guild_id not in self.server_settings:
            self.server_settings[guild_id] = {}

        self.server_settings[guild_id][module.lower()] = False
        self.save_settings()

        embed = discord.Embed(
            title="✅ Module Disabled",
            description=f"All {module.upper()} commands have been disabled for this server!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command(name="enable")
    @commands.has_permissions(administrator=True)
    async def enable_module(self, ctx: commands.Context, module: str):
        if module.lower() not in ['ai', 'game']:
            await ctx.send("Invalid module. Use 'ai' or 'game'.")
            return

        guild_id = str(ctx.guild.id)
        if guild_id not in self.server_settings:
            self.server_settings[guild_id] = {}

        self.server_settings[guild_id][module.lower()] = True
        self.save_settings()

        embed = discord.Embed(
            title="✅ Module Enabled",
            description=f"All {module.upper()} commands have been enabled for this server!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="status")
    @commands.has_permissions(administrator=True)
    async def module_status(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)
        
        ai_status = "✅ Enabled" if self.is_module_enabled(guild_id, "ai") else "❌ Disabled"
        game_status = "✅ Enabled" if self.is_module_enabled(guild_id, "game") else "❌ Disabled"

        embed = discord.Embed(
            title="Server Module Status",
            color=discord.Color.blue()
        )
        embed.add_field(name="AI Commands", value=ai_status, inline=True)
        embed.add_field(name="Game Commands", value=game_status, inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EnableDisable(bot))