import discord
from discord.ext import commands
from discord import app_commands
import logging
from .shop_helpers import (
    save_shops, 
    send_response, 
    get_user_aura_points, 
    handle_purchase, 
    load_shops, 
    load_aura_points, 
    save_aura_points
)

class BuyItem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="buyitem", aliases=["buy"])
    async def buy_item_command(self, ctx, *args):
        # Handle both "buy itemname" and "buy item itemname" formats
        if not args:
            await send_response(ctx, "Please specify an item to buy. Usage: `.buy <item name>` or `.buy item <item name>`")
            return
            
        if args[0].lower() == "item":
            name = " ".join(args[1:])  # Join remaining words as item name
        else:
            name = " ".join(args)  # Join all words as item name
            
        await self.buy_item_logic(ctx, name)

    @app_commands.command(name="buy_item", description="Buy an item from the Aura Shop")
    @app_commands.describe(name="The name of the item you want to buy")
    async def buy_item_slash(self, interaction: discord.Interaction, name: str):
        await self.buy_item_logic(interaction, name)

    async def buy_item_logic(self, ctx, name: str):
        try:
            guild_id = str(ctx.guild.id)
            user = ctx.author if isinstance(ctx, commands.Context) else ctx.user
            user_id = str(user.id)

            shops = await load_shops()
            aura_points = await load_aura_points()
            user_aura_points = get_user_aura_points(aura_points, user_id)

            if guild_id not in shops or not shops[guild_id]:
                embed = discord.Embed(
                    title="🛍️ Empty Shop",
                    description="The shop is currently empty. Please check back later!"
                )
                await send_response(ctx, embed=embed)
                return

            item_to_buy = next((item for item in shops[guild_id] 
                               if item["name"].lower() == name.lower()), None)
            
            if not item_to_buy:
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
                return

            # Check if user already has the role
            role = ctx.guild.get_role(item_to_buy['role_id'])
            if role in user.roles:
                await send_response(ctx, f"You already have the '{role.name}' role!")
                return

            if user_aura_points < item_to_buy['cost']:
                embed = discord.Embed(
                    title="❌ Insufficient Aura Points",
                    description=f"You need **{item_to_buy['cost'] - user_aura_points:,}** more Aura points to buy this item.",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="Your Balance", 
                    value=f"**{user_aura_points:,}** Aura points"
                )
                embed.add_field(
                    name="Item Cost", 
                    value=f"**{item_to_buy['cost']:,}** Aura points"
                )
                await send_response(ctx, embed=embed)
                return

            # Process the purchase
            aura_points[user_id] = user_aura_points - item_to_buy['cost']
            await save_aura_points(aura_points)
            
            try:
                await handle_purchase(user, item_to_buy)
            except discord.Forbidden:
                # Refund points if role assignment fails
                aura_points[user_id] = user_aura_points
                await save_aura_points(aura_points)
                await send_response(ctx, "Failed to assign the role. Please contact an administrator.")
                return

            embed = discord.Embed(
                title="✅ Purchase Successful",
                description=f"You bought **{item_to_buy['name']}** for **{item_to_buy['cost']:,}** Aura points!",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Remaining Balance", 
                value=f"**{aura_points[user_id]:,}** Aura points"
            )
            await send_response(ctx, embed=embed)

        except Exception as e:
            logging.error(f"Error in buy_item_logic: {e}")
            await send_response(ctx, "An error occurred while processing your request.")

async def setup(bot):
    await bot.add_cog(BuyItem(bot))
