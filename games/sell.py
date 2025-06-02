import discord
from discord.ext import commands
import json
import logging
from datetime import datetime
import asyncio
import random
import os
import shutil
from pathlib import Path

class BrainrotSell(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_logging()
        # Get absolute path to data directory relative to bot's root
        self.data_dir = Path('data').absolute()
        self.users_file = self.data_dir / 'users.json'
        self.characters_file = self.data_dir / 'characters.json'
        self.transactions_file = self.data_dir / 'transactions.json'
        self.aura_points_file = Path('aura_points.json').absolute()
        
        # Define point ranges for different card types
        self.point_ranges = {
            'normal': (100, 500),
            'legendary': (2000, 5000),
            'loser': (500, 1000)
        }
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize users.json with correct structure if needed
        if not self.users_file.exists():
            self.save_json_file(self.users_file, {"users": {}})
        
        # Load initial data
        self.user_data = self.load_user_data()
        self.logger.info(f"Loaded user data from {self.users_file}")
        
        self.active_sells = set()

    def setup_logging(self):
        """Setup enhanced logging configuration"""
        self.logger = logging.getLogger('brainrot_sell')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s:%(levelname)s:%(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def load_json_file(self, file_path, default_value):
        """Load JSON file with proper error handling"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return default_value

            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading {file_path}: {e}")
            return default_value

    def save_json_file(self, file_path, data):
        """Save JSON file with proper error handling"""
        try:
            file_path = Path(file_path)
            
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to temporary file first
            temp_path = file_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic rename
            temp_path.replace(file_path)
            
            return True
        except Exception as e:
            self.logger.error(f"Error saving {file_path}: {e}")
            if temp_path.exists():
                temp_path.unlink()
            return False

    def load_user_data(self):
        """Load user data with validation"""
        try:
            if not self.users_file.exists():
                default_data = {"users": {}}
                self.save_json_file(self.users_file, default_data)
                return default_data

            with open(self.users_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, dict) or "users" not in data:
                self.logger.error("Invalid user data structure")
                return {"users": {}}
                
            # Clean and validate user data
            for user_id in list(data["users"].keys()):
                if "claimed_characters" not in data["users"][user_id]:
                    data["users"][user_id]["claimed_characters"] = {}
                elif not isinstance(data["users"][user_id]["claimed_characters"], dict):
                    data["users"][user_id]["claimed_characters"] = {}
                
                # Remove any empty character entries
                claimed_chars = data["users"][user_id]["claimed_characters"]
                data["users"][user_id]["claimed_characters"] = {
                    k: v for k, v in claimed_chars.items() 
                    if isinstance(v, int) and v > 0
                }
                
                # Remove user if they have no characters
                if not data["users"][user_id]["claimed_characters"]:
                    if "last_claim" not in data["users"][user_id]:
                        del data["users"][user_id]
                
            # Save cleaned data
            self.save_json_file(self.users_file, data)
            return data
        
        except Exception as e:
            self.logger.error(f"Error loading user data: {e}")
            return {"users": {}}

    def save_user_data(self, data):
        """Save user data with validation and backup"""
        try:
            if not isinstance(data, dict) or "users" not in data:
                self.logger.error("Invalid user data structure, aborting save")
                return False
            
            # Ensure directory exists
            self.data_dir.mkdir(exist_ok=True)
            
            # Create backup before saving
            if self.users_file.exists():
                backup_path = self.users_file.with_suffix('.backup')
                shutil.copy2(self.users_file, backup_path)
            
            # Write to temporary file first
            temp_file = self.users_file.with_suffix('.tmp')
            
            try:
                # Ensure the data is properly formatted
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())
                
                # Use shutil.move for atomic operation
                shutil.move(str(temp_file), str(self.users_file))
                
                # Update the in-memory data
                self.user_data = data
                
                self.logger.info(f"User data saved successfully to {self.users_file}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error during file write: {e}")
                if temp_file.exists():
                    temp_file.unlink()
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to save user data: {e}")
            # Try to restore from backup if save failed
            if 'backup_path' in locals() and backup_path.exists():
                try:
                    shutil.copy2(backup_path, self.users_file)
                    self.logger.info("Restored from backup after failed save")
                except Exception as backup_error:
                    self.logger.error(f"Failed to restore backup: {backup_error}")
            return False

    def load_character_data(self):
        """Load character data with validation"""
        data = self.load_json_file(self.characters_file, {"characters": []})
        if isinstance(data, dict) and "characters" in data:
            return data["characters"]
        return []

    def load_aura_points(self):
        """Load aura points with validation"""
        return self.load_json_file(self.aura_points_file, {})

    def save_aura_points(self, data):
        """Save aura points with validation"""
        if not isinstance(data, dict):
            self.logger.error("Invalid aura points data structure")
            return False
        return self.save_json_file(self.aura_points_file, data)

    def update_user_aura(self, user_id: str, points: int):
        """Update user aura points with validation"""
        aura_data = self.load_aura_points()
        user_id_str = str(user_id)
        
        if not isinstance(points, int):
            self.logger.error(f"Invalid points value for user {user_id}: {points}")
            return False
            
        if user_id_str not in aura_data:
            aura_data[user_id_str] = 0
        
        aura_data[user_id_str] += points
        return self.save_aura_points(aura_data)

    def get_card_details(self, card_id):
        """Get card details with validation"""
        characters = self.load_character_data()
        return next((char for char in characters if str(char.get('id', '')) == str(card_id)), None)

    def calculate_points(self, card_type, count=1):
        """Calculate points with validation"""
        if not isinstance(count, int) or count < 1:
            self.logger.error(f"Invalid count value: {count}")
            return 0
            
        min_points, max_points = self.point_ranges.get(card_type, (100, 500))
        points = random.randint(min_points, max_points)
        return points * count

    def record_transaction(self, user_id, card_id, points, count):
        """Record transaction with validation"""
        try:
            transactions = self.load_json_file(self.transactions_file, [])
            
            transaction = {
                "user_id": str(user_id),
                "card_id": str(card_id),
                "points": points,
                "count": count,
                "timestamp": datetime.now().isoformat()
            }
            
            transactions.append(transaction)
            
            # Ensure directory exists
            self.data_dir.mkdir(exist_ok=True)
            
            # Write to temporary file first
            temp_file = self.transactions_file.with_suffix('.tmp')
            
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(transactions, f, indent=2, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())
                
                # Use shutil.move for atomic operation
                shutil.move(str(temp_file), str(self.transactions_file))
                
                self.logger.info(f"Transaction recorded for user {user_id}: {card_id} x{count} for {points} points")
                return True
                
            except Exception as e:
                self.logger.error(f"Error saving transaction: {e}")
                if temp_file.exists():
                    temp_file.unlink()
                return False
                
        except Exception as e:
            self.logger.error(f"Error recording transaction: {e}")
            return False

    @commands.command(name="sell")
    async def sell(self, ctx, card_id: str, count: int = None):
        user_id = str(ctx.author.id)
        
        if user_id in self.active_sells:
            await ctx.send("❌ You already have an active sell operation. Please complete or cancel it before starting a new one.")
            return
        
        self.active_sells.add(user_id)
        self.logger.info(f"User {user_id} started a sell operation for {card_id}")

        try:
            if card_id.lower() == "all":
                await self.sell_all_cards(ctx)
                return

            # Load fresh data
            data = self.load_user_data()
            
            # Initialize user data if not exists
            if user_id not in data["users"]:
                data["users"][user_id] = {"claimed_characters": {}}
            elif "claimed_characters" not in data["users"][user_id]:
                data["users"][user_id]["claimed_characters"] = {}

            card_details = self.get_card_details(card_id)
            if not card_details:
                await ctx.send("❌ Error finding card details!")
                self.logger.error(f"Card details not found for ID {card_id}")
                return

            if card_details['type'] == 'loser':
                await ctx.send("❌ Loser cards cannot be sold! They stay in your inventory forever!")
                return

            # Get fresh user data
            user_data = data["users"][user_id]
            owned_count = user_data["claimed_characters"].get(str(card_id), 0)

            if owned_count == 0:
                await ctx.send(f"❌ You don't own any cards with ID #{card_id}!")
                return

            if count is None:
                count = owned_count
            elif count > owned_count:
                await ctx.send(f"❌ You only have {owned_count} cards with ID #{card_id}!")
                return

            points = self.calculate_points(card_details['type'], count)

            # Create confirmation embed
            embed = discord.Embed(
                title="🎴 Sell Cards - Confirmation",
                description=f"You are about to sell {count}x cards."
            )
            embed.add_field(
                name="Transaction Details",
                value=f"```• Selling: {count}x #{card_id} ({card_details['name']})\n• Type: {card_details['type'].capitalize()}\n• Value: {points:,} points```",
                inline=False
            )
            embed.set_footer(text="React with ✅ to confirm or ❌ to cancel")
            confirm_msg = await ctx.send(embed=embed)

            await confirm_msg.add_reaction("✅")
            await confirm_msg.add_reaction("❌")

            try:
                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] \
                           and reaction.message.id == confirm_msg.id

                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)

                if str(reaction.emoji) == "✅":
                    # Reload data to ensure we have the latest state
                    data = self.load_user_data()
                    
                    # Make sure user data exists
                    if user_id not in data["users"]:
                        data["users"][user_id] = {"claimed_characters": {}}
                    if "claimed_characters" not in data["users"][user_id]:
                        data["users"][user_id]["claimed_characters"] = {}
                    
                    user_data = data["users"][user_id]
                    current_count = user_data["claimed_characters"].get(str(card_id), 0)
                    
                    if current_count < count:
                        await confirm_msg.edit(content="❌ Error: Card count has changed. Please try again.")
                        return

                    # Update the card count
                    if count == current_count:
                        del user_data["claimed_characters"][str(card_id)]
                    else:
                        user_data["claimed_characters"][str(card_id)] = current_count - count

                    # Save changes and update points
                    if self.save_user_data(data):
                        if self.update_user_aura(user_id, points):
                            # Show success message
                            aura_data = self.load_aura_points()
                            new_balance = aura_data.get(str(user_id), 0)

                            success_embed = discord.Embed(
                                title="💰 Card Sold Successfully"
                            )
                            success_embed.add_field(
                                name="Transaction Details",
                                value=f"```• Sold: {count}x #{card_id} ({card_details['name']})\n• Type: {card_details['type'].capitalize()}\n• Earned: {points:,} aura points```",
                                inline=False
                            )
                            success_embed.add_field(
                                name="Balance",
                                value=f"```New Balance: {new_balance:,} points```",
                                inline=False
                            )
                            success_embed.set_footer(text=f"Sold by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
                            await confirm_msg.edit(embed=success_embed)
                            self.record_transaction(user_id, card_id, points, count)
                            self.logger.info(f"User {user_id} successfully sold {count}x #{card_id} for {points} points")
                        else:
                            await confirm_msg.edit(content="❌ Error updating aura points.")
                    else:
                        await confirm_msg.edit(content="❌ Error saving inventory changes.")
                else:
                    await confirm_msg.edit(content="❌ Sale cancelled.")

            except asyncio.TimeoutError:
                await confirm_msg.edit(content="❌ Sale cancelled - timeout reached.")

        except Exception as e:
            self.logger.error(f"Error in sell command: {e}")
            await ctx.send("❌ An error occurred while processing the sale.")
        
        finally:
            self.active_sells.remove(user_id)
            try:
                await confirm_msg.clear_reactions()
            except:
                pass

    async def sell_all_cards(self, ctx):
        user_id = str(ctx.author.id)
        self.logger.info(f"User {user_id} initiated sell all operation")

        # Load fresh data
        data = self.load_user_data()
        if user_id not in data["users"] or not data["users"][user_id].get("claimed_characters", {}):
            await ctx.send("❌ You don't have any cards to sell!")
            return

        user_data = data["users"][user_id]
        characters = self.load_character_data()
        
        total_points = 0
        card_summary = []
        kept_cards = {}
        last_claim = user_data.get("last_claim", None)

        # Calculate points and prepare summary
        for card_id, count in user_data["claimed_characters"].items():
            card_details = next((char for char in characters if str(char['id']) == str(card_id)), None)
            if card_details:
                if card_details['type'] == 'loser':
                    kept_cards[card_id] = count
                    card_summary.append(f"{count}x {card_details['name']} (KEPT - Loser Card)")
                else:
                    points = self.calculate_points(card_details['type'], count)
                    total_points += points
                    card_summary.append(f"{count}x {card_details['name']} ({points:,} points)")

        # Create confirmation embed
        embed = discord.Embed(
            title="🎴 Sell All Cards - Confirmation",
            description="You are about to sell all your non-loser cards."
        )
        embed.add_field(
            name="Transaction Summary",
            value=f"```• Total Cards: {len(card_summary)}\n• Total Value: {total_points:,} points```",
            inline=False
        )
        embed.add_field(
            name="Card Details",
            value="```" + "\n".join(card_summary[:10]) + ("..." if len(card_summary) > 10 else "") + "```",
            inline=False
        )
        embed.set_footer(text="React with ✅ to confirm or ❌ to cancel")
        confirm_msg = await ctx.send(embed=embed)

        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")

        try:
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] \
                       and reaction.message.id == confirm_msg.id

            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)

            if str(reaction.emoji) == "✅":
                # Reload fresh data
                data = self.load_user_data()
                if user_id not in data["users"]:
                    data["users"][user_id] = {}
                
                # Create new inventory with only loser cards
                new_inventory = {}
                for card_id, count in data["users"][user_id].get("claimed_characters", {}).items():
                    card_details = next((char for char in characters if str(char['id']) == str(card_id)), None)
                    if card_details and card_details['type'] == 'loser':
                        new_inventory[card_id] = count
                
                # Update user's inventory to only keep loser cards and preserve last_claim
                data["users"][user_id] = {
                    "claimed_characters": new_inventory,
                    "last_claim": last_claim
                }
                
                # Ensure proper saving of changes
                if not self.save_user_data(data):
                    await confirm_msg.edit(content="❌ Error saving inventory changes.")
                    return
                    
                if not self.update_user_aura(user_id, total_points):
                    await confirm_msg.edit(content="❌ Error updating aura points.")
                    return

                aura_data = self.load_aura_points()
                new_balance = aura_data.get(str(user_id), 0)

                result_embed = discord.Embed(
                    title="💰 All Cards Sold!"
                )
                result_embed.add_field(
                    name="Transaction Details",
                    value=f"```• Sold: All non-loser cards\n• Earned: {total_points:,} aura points```",
                    inline=False
                )
                result_embed.add_field(
                    name="Balance",
                    value=f"```New Balance: {new_balance:,} points```",
                    inline=False
                )
                result_embed.set_footer(text=f"Sold by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
                await confirm_msg.edit(embed=result_embed)
                self.record_transaction(user_id, 'all', total_points, len(card_summary))
                self.logger.info(f"User {user_id} successfully sold all cards for {total_points} points")
            else:
                await confirm_msg.edit(content="❌ Sale cancelled.")
                self.logger.info(f"User {user_id} cancelled the sell all operation")

        except asyncio.TimeoutError:
            await confirm_msg.edit(content="❌ Sale cancelled - timeout reached.")
            self.logger.info(f"Sell all timeout for user {user_id}")

        try:
            await confirm_msg.clear_reactions()
        except:
            pass

    @commands.command(name="sellpreview")
    async def sell_preview(self, ctx, *card_ids):
        user_id = str(ctx.author.id)
        self.logger.info(f"User {user_id} requested sell preview for {card_ids}")
        data = self.load_user_data()
        
        if user_id not in data["users"]:
            await ctx.send("❌ You don't have any cards to sell!")
            return

        user_data = data["users"][user_id]
        characters = self.load_character_data()
        
        total_points = 0
        preview_data = []

        for card_id in card_ids:
            card_details = next((char for char in characters if str(char['id']) == str(card_id)), None)
            if card_details:
                owned_count = user_data.get("claimed_characters", {}).get(str(card_id), 0)
                if owned_count > 0:
                    points = self.calculate_points(card_details['type'], owned_count)
                    total_points += points
                    preview_data.append(f"{owned_count}x #{card_id} ({card_details['name']}) - {points:,} points")

        if not preview_data:
            await ctx.send("❌ You don't own any of the specified cards!")
            return

        embed = discord.Embed(
            title="🔍 Sell Preview",
            description="Here's a preview of what you could sell:"
        )
        embed.add_field(
            name="Cards",
            value="```" + "\n".join(preview_data) + "```",
            inline=False
        )
        embed.add_field(
            name="Total Value",
            value=f"```{total_points:,} points```",
            inline=False
        )
        embed.set_footer(text="Use the sell command to actually sell these cards.")
        await ctx.send(embed=embed)
        self.logger.info(f"Sell preview sent to user {user_id}")

async def setup(bot):
    await bot.add_cog(BrainrotSell(bot))