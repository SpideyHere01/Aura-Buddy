import discord
from discord.ext import commands
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

class InventoryView(discord.ui.View):
    def __init__(self, cog, user_id: str, character_type: str = "All"):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
        self.invoker_id = None  # Will store the ID of who invoked the command
        self.current_page = 0
        self.items_per_page = 5
        self.character_type = character_type
        self.update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.invoker_id:
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

    @discord.ui.select(
        placeholder="Filter by type",
        options=[
            discord.SelectOption(label="All", value="All"),
            discord.SelectOption(label="Legendary", value="legendary"),
            discord.SelectOption(label="Normal", value="normal"),
            discord.SelectOption(label="Loser", value="loser")
        ]
    )
    async def select_type(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.character_type = select.values[0]
        self.current_page = 0 
        await self.update_inventory_message(interaction)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.gray, disabled=True)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        await self.update_inventory_message(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.gray, disabled=True)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        await self.update_inventory_message(interaction)

    def update_buttons(self):
        total_items = len(self.get_filtered_inventory())
        total_pages = (total_items - 1) // self.items_per_page + 1

        self.prev_button.disabled = self.current_page <= 0
        self.next_button.disabled = self.current_page >= total_pages - 1

    def get_filtered_inventory(self) -> List[Dict]:
        inventory = []
        user_data = self.cog.get_user_inventory(self.user_id)
        char_data = self.cog.get_character_data()

        if not user_data or not char_data:
            return []

        for card_id, count in user_data.items():
            char_info = next((c for c in char_data["characters"] if c["id"] == card_id), None)
            if char_info:
                if self.character_type == "All" or char_info["type"] == self.character_type:
                    inventory.append({**char_info, "count": count})

        return inventory

    async def update_inventory_message(self, interaction: discord.Interaction):
        self.update_buttons()
        embed = self.cog.create_inventory_embed(
            self.user_id,
            self.current_page,
            self.items_per_page,
            self.get_filtered_inventory(),
            self.character_type
        )
        await interaction.response.edit_message(embed=embed, view=self)

class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('inventory')
        self.data_dir = Path('data').absolute()
        self.users_file = self.data_dir / 'users.json'
        self.characters_file = self.data_dir / 'characters.json'
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)

    def load_data(self) -> tuple:
        """Load both user and character data"""
        try:
            if not self.users_file.exists():
                users_data = {"users": {}}
            else:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    users_data = json.load(f)
                    # Validate and fix user data structure
                    if not isinstance(users_data, dict) or "users" not in users_data:
                        users_data = {"users": {}}
                    # Ensure each user has proper structure
                    for user_id in users_data["users"]:
                        if "claimed_characters" not in users_data["users"][user_id]:
                            users_data["users"][user_id]["claimed_characters"] = {}
                
            with open(self.characters_file, 'r', encoding='utf-8') as f:
                chars_data = json.load(f)
                
            return users_data, chars_data
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            return {"users": {}}, {"characters": []}

    def get_user_inventory(self, user_id: str) -> Dict:
        """Get user's inventory with fresh data"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
                user_data = users_data.get("users", {}).get(str(user_id), {})
                return user_data.get("claimed_characters", {})
        except Exception as e:
            self.logger.error(f"Error loading user inventory: {e}")
            return {}

    def get_character_data(self) -> Dict:
        _, chars_data = self.load_data()
        return chars_data

    def create_inventory_embed(self, user_id: str, page: int, items_per_page: int, 
                             inventory: List[Dict], filter_type: str) -> discord.Embed:
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        current_items = inventory[start_idx:end_idx]
        
        embed = discord.Embed(
            title="Character Collection",
            description=f"Filter: {filter_type}"
        )
        
        if not current_items:
            embed.description = "No characters found!"
            return embed

        for item in current_items:
            rarity_text = {
                'legendary': '[L]',
                'normal': '[N]',
                'loser': '[X]'
            }.get(item['type'], '[N]')
            
            embed.add_field(
                name=f"{rarity_text} {item['name']} #{item['id']}",
                value=f"Type: {item['type'].capitalize()}\nOwned: x{item['count']}",
                inline=False
            )

        total_pages = (len(inventory) - 1) // items_per_page + 1
        embed.set_footer(
            text=f"Page {page + 1}/{total_pages} • Total Cards: {len(inventory)}"
        )
        return embed

    @commands.command(name="inventory", aliases=["inv"])
    async def show_inventory(self, ctx, member: Optional[discord.Member] = None):
        """Display a user's card inventory"""
        target = member if member else ctx.author
        view = InventoryView(self, str(target.id))
        view.invoker_id = ctx.author.id  # Set the invoker's ID
        embed = self.create_inventory_embed(
            str(target.id),
            0,
            view.items_per_page,
            view.get_filtered_inventory(),
            "All"
        )
        message = await ctx.send(embed=embed, view=view)
        view.message = message  # Store message reference for timeout handling

    async def handle_inventory_error(self, ctx):
        await ctx.send("Failed to load inventory. Please try again.")

async def setup(bot):
    await bot.add_cog(Inventory(bot))
