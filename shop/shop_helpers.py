import discord
import logging
import os  # Imported os to handle file paths
from discord.ext import commands
from db.mongo import shops_collection, aura_points_collection  # Updated imports

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to load shops from MongoDB
async def load_shops():
    try:
        cursor = shops_collection.find({})
        shops = {}
        async for doc in cursor:
            shops[doc['_id']] = doc.get('items', [])
        logging.info("Shops loaded successfully from MongoDB.")
        return shops
    except Exception as e:
        logging.error(f"Error loading shops from MongoDB: {e}")
        return {}

# Function to save shops to MongoDB
async def save_shops(shops):
    try:
        for guild_id, items in shops.items():
            await shops_collection.update_one(
                {"_id": guild_id},
                {"$set": {"items": items}},
                upsert=True
            )
        logging.info("Shops saved successfully to MongoDB.")
    except Exception as e:
        logging.error(f"Error saving shops to MongoDB: {e}")

# Function to load aura points from MongoDB
async def load_aura_points():
    try:
        aura_points = {}
        cursor = aura_points_collection.find({})
        async for doc in cursor:
            # Changed from doc['_id'] to doc['user_id']
            aura_points[doc['user_id']] = doc.get('points', 0)
        logging.info("Aura points loaded successfully from MongoDB.")
        return aura_points
    except Exception as e:
        logging.error(f"Error loading aura points from MongoDB: {e}")
        return {}

# Function to save aura points to MongoDB
async def save_aura_points(aura_points):
    try:
        for user_id, points in aura_points.items():
            # Changed from {"_id": user_id} to {"user_id": user_id}
            await aura_points_collection.update_one(
                {"user_id": user_id},
                {"$set": {"points": points}},
                upsert=True
            )
        logging.info("Aura points saved successfully to MongoDB.")
    except Exception as e:
        logging.error(f"Error saving aura points to MongoDB: {e}")

# Function to send responses, handling both context and interaction types
async def send_response(ctx, content=None, embed=None):
    try:
        if isinstance(ctx, discord.Interaction):
            if ctx.response.is_done():
                await ctx.followup.send(content=content, embed=embed)
            else:
                await ctx.response.send_message(content=content, embed=embed)
        else:
            await ctx.send(content=content, embed=embed)
    except discord.Forbidden:
        logging.warning("Failed to send message due to missing permissions.")
    except Exception as e:
        logging.error(f"Error in send_response: {e}")

# Function to retrieve a user's Aura points
def get_user_aura_points(aura_points, member_id):
    return aura_points.get(str(member_id), 0)

# Function to handle item purchases, specifically for roles
async def handle_purchase(member, item):
    guild = member.guild
    role = guild.get_role(item['role_id'])
    if role:
        await member.add_roles(role)
        await member.send(f"You have received the role '{role.name}' in **{guild.name}**!")
    else:
        await member.send(f"Role with ID '{item['role_id']}' not found in the server **{guild.name}**.")

class ShopHelpers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

# Asynchronous setup function for the cog
async def setup(bot):
    await bot.add_cog(ShopHelpers(bot))
