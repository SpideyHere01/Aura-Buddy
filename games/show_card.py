import discord
from discord.ext import commands
import json
import os

class ShowCard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.drop_cog = None

    async def cog_load(self):
        self.drop_cog = self.bot.get_cog('BrainrotDrop')

    @commands.command(name="show")
    async def show_card(self, ctx, card_id: str):
        if not self.drop_cog:
            self.drop_cog = self.bot.get_cog('BrainrotDrop')
            if not self.drop_cog:
                await ctx.send("Unable to access card generation system")
                return

        try:
            with open('data/characters.json', 'r', encoding='utf-8') as f:
                characters = json.load(f).get("characters", [])
                character = next((c for c in characters if c['id'] == card_id), None)

            if not character:
                await ctx.send(f"No character found with ID #{card_id}")
                return

            card_path = await self.drop_cog.generate_card(character)
            if not card_path or not os.path.exists(card_path):
                await ctx.send("Error generating card image")
                return

            try:
                await ctx.send(file=discord.File(card_path))
            finally:
                try:
                    os.remove(card_path)
                except Exception as e:
                    print(f"Error cleaning up card file: {e}")

        except Exception as e:
            await ctx.send(f"Error showing card: {e}")

async def setup(bot):
    await bot.add_cog(ShowCard(bot))