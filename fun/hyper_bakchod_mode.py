import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timedelta

class UltraBakchodMode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bakchod_mode = False
        self.bakchod_channels = set()
        self.last_nickname_change = datetime.now()
        self.last_channel_change = datetime.now()
        # ... (rest of the __init__ method remains the same)

    @commands.command(name='ultra_bakchod_on', help="Activate Ultra Bakchod Mode")
    async def ultra_bakchod_on_command(self, ctx):
        await self.ultra_bakchod_on_logic(ctx)

    @app_commands.command(name='ultra_bakchod_on', description="Activate Ultra Bakchod Mode")
    async def ultra_bakchod_on_slash(self, interaction: discord.Interaction):
        await self.ultra_bakchod_on_logic(interaction)

    async def ultra_bakchod_on_logic(self, ctx):
        if self.bakchod_mode:
            await self.send_response(ctx, "🔥 **SYSTEM ALREADY PEAK COMEDY PE HAI!**\nGrass? Touch? More like **GRASS KA MASS** 🌿")
            return

        self.bakchod_mode = True
        self.bakchod_channels.add(ctx.channel.id)
        
        startup_messages = [
            "🔥 **ULTRA BAKCHODI PRO MAX 5G LAUNCHED!**\nPerformance: **UNLIMITED**\nRizz: **MAXIMUM**\nTouch Grass: **IMPOSSIBLE** 🚀",
            "⚡ **BAKCHODI ENGINE V69.420 INITIALIZED**\nStatus: **PEAK COMEDY**\nGrass: **UNTOUCHED**\nSigma Level: **MAXIMUM** 💀",
            "☢️ **COMEDY VIRUS DETECTED**\nInfection Rate: **100%**\nCure: **NO**\nGrass: **404 NOT FOUND** 🗿"
        ]
        
        await self.send_response(ctx, random.choice(startup_messages))
        await self.start_bakchodi(ctx.channel)

    @commands.command(name='ultra_bakchod_off', help="Deactivate Ultra Bakchod Mode")
    async def ultra_bakchod_off_command(self, ctx):
        await self.ultra_bakchod_off_logic(ctx)

    @app_commands.command(name='ultra_bakchod_off', description="Deactivate Ultra Bakchod Mode")
    async def ultra_bakchod_off_slash(self, interaction: discord.Interaction):
        await self.ultra_bakchod_off_logic(interaction)

    async def ultra_bakchod_off_logic(self, ctx):
        if not self.bakchod_mode:
            shutdown_fails = [
                "Bro system already **DED** hai! Just like your rizz! 💀",
                "Error 404: **BAKCHODI.exe** not found! Touch some grass instead! 🌿",
                "**Task Failed Successfully**: Can't stop what's already stopped! 🤡"
            ]
            await self.send_response(ctx, random.choice(shutdown_fails))
            return

        self.bakchod_mode = False
        self.bakchod_channels.clear()
        
        shutdown_messages = [
            "**BAKCHODI.exe** has stopped! Windows XP shutdown earrape plays... 🎵",
            "**COMEDY ENGINE** shutting down! Touch grass protocol activated! 🌿",
            "Understandable, have a **GREAT L** 🗿"
        ]
        await self.send_response(ctx, random.choice(shutdown_messages))

    async def send_response(self, ctx, message):
        if isinstance(ctx, discord.Interaction):
            await ctx.response.send_message(message)
        else:
            await ctx.send(message)

    # ... (rest of the methods remain the same)

    @commands.Cog.listener()
    async def on_message(self, message):
        if (self.bakchod_mode and 
            message.channel.id in self.bakchod_channels and 
            not message.author.bot):
            
            if random.random() < 0.15:
                await asyncio.sleep(random.uniform(0.5, 2))
                try:
                    await message.add_reaction(random.choice(self.emojis))
                except:
                    pass
                
            if random.random() < 0.08:
                await asyncio.sleep(random.uniform(1, 3))
                await self.do_random_bakchodi(message.channel)

async def setup(bot):
    await bot.add_cog(UltraBakchodMode(bot))