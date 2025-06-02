import discord
from discord.ext import commands
from discord import app_commands
import logging
from .shop_helpers import (
    send_response,
    load_shops,
    save_shops
)

class AddItem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="additem", aliases=["add"])
    @commands.has_permissions(administrator=True)
    async def add_item_command(self, ctx, *args):
        # Handle both "add role cost" and "add item role cost" formats
        try:
            if len(args) < 2:
                await send_response(ctx, "Please provide both a role and cost. Usage: `.add <role> <cost>` or `.add item <role> <cost>`")
                return
                
            if args[0].lower() == "item":
                args = args[1:]  # Remove "item" from args
                
            # Get role from mention or name
            role_mention = args[0]
            try:
                role = await commands.RoleConverter().convert(ctx, role_mention)
            except commands.RoleNotFound:
                await send_response(ctx, f"Could not find role: {role_mention}")
                return
                
            cost = int(args[-1])
            await self.add_item_logic(ctx, role, cost)
        except ValueError:
            await send_response(ctx, "Invalid cost value. Please provide a number.")

    @app_commands.command(name="add_item", description="Add an item to the shop")
    @app_commands.describe(
        role="The role to add as an item",
        cost="The cost in Aura points"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_item_slash(self, interaction: discord.Interaction, role: discord.Role, cost: int):
        await self.add_item_logic(interaction, role, cost)

    async def add_item_logic(self, ctx, role: discord.Role, cost: int):
        try:
            # Validate role hierarchy
            if isinstance(ctx, discord.Interaction):
                author = ctx.user
            else:
                author = ctx.author
                
            if role >= author.top_role and not author.guild_permissions.administrator:
                await send_response(ctx, "You cannot add a role that is higher than or equal to your highest role.")
                return

            # Validate cost range
            if cost < 1:
                await send_response(ctx, "Cost must be at least 1 Aura point.")
                return
            
            if cost > 1000000:  # Add reasonable upper limit
                await send_response(ctx, "Cost cannot exceed 1,000,000 Aura points.")
                return

            shops = await load_shops()
            guild_id = str(ctx.guild.id)
            logging.info(f"AddItem - Guild ID: {guild_id}")

            if guild_id not in shops:
                shops[guild_id] = []

            # Check if item already exists
            if any(item["role_id"] == role.id for item in shops[guild_id]):
                await send_response(ctx, f"The role '{role.name}' is already in the shop.")
                return

            item = {
                "name": role.name,
                "role_id": role.id,
                "cost": cost
            }

            shops[guild_id].append(item)
            await save_shops(shops)
            embed = discord.Embed(
                title="✅ Item Added",
                description=f"Successfully added **{role.name}** to the shop!"
            )
            embed.add_field(
                name="Item Details",
                value=f"**Role:** {role.mention}\n"
                      f"**Cost:** {cost:,} Aura points",
                inline=False
            )
            await send_response(ctx, embed=embed)
        except Exception as e:
            await send_response(ctx, "An error occurred while processing your request.")
            logging.error(f"Error in add_item_logic: {e}")

    @add_item_command.error
    async def add_item_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await send_response(ctx, "You do not have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await send_response(ctx, "Invalid arguments provided. Please mention a valid role and specify the cost.")
        else:
            await send_response(ctx, "An error occurred while processing your request.")
            logging.error(f"Error in add_item_command: {error}")

    @add_item_slash.error
    async def add_item_slash_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await send_response(interaction, "You do not have permission to use this command.")
        else:
            await send_response(interaction, "An error occurred while processing your request.")
            logging.error(f"Error in add_item_slash: {error}")

async def setup(bot):
    await bot.add_cog(AddItem(bot))
