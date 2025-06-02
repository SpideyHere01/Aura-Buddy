import discord
from discord.ext import commands
from discord import app_commands
import logging
from .shop_helpers import load_shops, save_shops, send_response

class RemoveItem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="removeitem", aliases=["remove"])
    @commands.has_permissions(administrator=True)
    async def remove_item_command(self, ctx, *args):
        # Handle both "remove itemname" and "remove item itemname" formats
        if not args:
            await send_response(ctx, "Please specify an item to remove. Usage: `.remove <item name>` or `.remove item <item name>`")
            return
            
        if args[0].lower() == "item":
            name = " ".join(args[1:])  # Join remaining words as item name
        else:
            name = " ".join(args)  # Join all words as item name
            
        await self.remove_item_logic(ctx, name)

    @app_commands.command(name="remove_item", description="Remove an item from the shop")
    @app_commands.describe(name="The name of the item to remove")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_item_slash(self, interaction: discord.Interaction, name: str):
        await self.remove_item_logic(interaction, name)

    async def remove_item_logic(self, ctx, name):
        try:
            shops = await load_shops()
            guild_id = str(ctx.guild.id)
            
            if guild_id not in shops or not shops[guild_id]:
                embed = discord.Embed(
                    title="🛍️ Shop Empty",
                    description="There are no items in the shop to remove."
                )
                await send_response(ctx, embed=embed)
                return

            item_to_remove = next((item for item in shops[guild_id] if item["name"].lower() == name.lower()), None)
            
            if item_to_remove:
                role = ctx.guild.get_role(item_to_remove['role_id'])
                shops[guild_id].remove(item_to_remove)
                await save_shops(shops)
                
                embed = discord.Embed(
                    title="✅ Item Removed",
                    description=f"Successfully removed **{item_to_remove['name']}** from the shop."
                )
                embed.add_field(
                    name="Item Details",
                    value=f"**Name:** {item_to_remove['name']}\n"
                          f"**Role:** {role.mention if role else 'Unknown Role'}\n"
                          f"**Cost:** {item_to_remove['cost']:,} Aura points"
                )
                await send_response(ctx, embed=embed)
            else:
                similar_items = [item["name"] for item in shops[guild_id] 
                               if name.lower() in item["name"].lower()]
                
                embed = discord.Embed(
                    title="❌ Item Not Found",
                    description=f"No item named '**{name}**' was found in the shop."
                )
                if similar_items:
                    embed.add_field(
                        name="Did you mean?",
                        value="\n".join(f"• {item}" for item in similar_items)
                    )
                await send_response(ctx, embed=embed)

        except Exception as e:
            logging.error(f"Error in remove_item_logic: {e}")
            await send_response(ctx, "An error occurred while removing the item.")

    @remove_item_command.error
    async def remove_item_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You need administrator permissions to remove items from the shop."
            )
            await send_response(ctx, embed=embed)
        else:
            await send_response(ctx, "An error occurred while processing your request.")
            logging.error(f"Error in remove_item_command: {error}")

    @remove_item_slash.error
    async def remove_item_slash_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You need administrator permissions to remove items from the shop."
            )
            await send_response(interaction, embed=embed)
        else:
            await send_response(interaction, "An error occurred while processing your request.")
            logging.error(f"Error in remove_item_slash: {error}")

async def setup(bot):
    await bot.add_cog(RemoveItem(bot))
