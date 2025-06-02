import discord
from discord.ext import commands
from discord import app_commands
import logging
from .shop_helpers import (
    send_response,
    load_shops,
    load_aura_points,
    get_user_aura_points
)

class ShowShop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="shop", aliases=["ashop"])
    async def show_shop_command(self, ctx, *args):
        # Handle both "shop" and "aura shop" formats
        if len(args) == 0 or (len(args) == 2 and args[0].lower() == "aura" and args[1].lower() == "shop"):
            await self.show_shop_logic(ctx)
        else:
            await send_response(ctx, "Invalid command. Use `.shop` or `.aura shop`")

    @app_commands.command(name="shop", description="Browse the Aura Shop")
    async def show_shop_slash(self, interaction: discord.Interaction):
        await self.show_shop_logic(interaction)

    async def show_shop_logic(self, ctx):
        try:
            shops = await load_shops()
            guild_id = str(ctx.guild.id)
            
            user_id = str(ctx.author.id) if isinstance(ctx, commands.Context) else str(ctx.user.id)
            aura_points = await load_aura_points()
            user_balance = get_user_aura_points(aura_points, user_id)

            if guild_id not in shops or not shops[guild_id]:
                embed = discord.Embed(
                    title="🛍️ Aura Shop",
                    description="The shop is currently empty."
                )
                if ctx.guild.me.guild_permissions.administrator:
                    embed.add_field(
                        name="ℹ️ Admin Info",
                        value="Use `/add_item` to add items to the shop!",
                        inline=False
                    )
                await send_response(ctx, embed=embed)
                return

            embed = discord.Embed(
                title="🛍️ Aura Shop",
                description="Welcome to the Aura Shop! Browse and purchase items below."
            )

            # Add user's balance with formatting
            embed.add_field(
                name="💰 Your Balance",
                value=f"**{user_balance:,}** Aura points",
                inline=False
            )

            # Add a separator
            embed.add_field(
                name="📦 Available Items",
                value="─" * 20,
                inline=False
            )

            # Group items by affordability
            affordable_items = []
            unaffordable_items = []
            
            for item in shops[guild_id]:
                role = ctx.guild.get_role(item['role_id'])
                if role:
                    item_display = (
                        f"**{item['name']}**\n"
                        f"Role: {role.mention}\n"
                        f"Cost: **{item['cost']:,}** Aura points"
                    )
                    
                    if user_balance >= item['cost']:
                        affordable_items.append(item_display)
                    else:
                        unaffordable_items.append(f"❌ {item_display}")

            # Add affordable items first
            if affordable_items:
                embed.add_field(
                    name="🟢 Items You Can Afford",
                    value="\n\n".join(affordable_items),
                    inline=False
                )

            # Then add unaffordable items
            if unaffordable_items:
                embed.add_field(
                    name="🔴 Items You Need More Points For",
                    value="\n\n".join(unaffordable_items),
                    inline=False
                )

            embed.set_footer(text="Use /buy_item <name> to purchase an item")
            await send_response(ctx, embed=embed)

        except Exception as e:
            logging.error(f"Error in show_shop_logic: {e}")
            await send_response(ctx, "An error occurred while displaying the shop.")

async def setup(bot):
    await bot.add_cog(ShowShop(bot))
