import discord
from discord.ext import commands
from discord import app_commands
import time

class CommonCommands(commands.Cog, name="Common Commands"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='ping', help="Check the bot's latency")
    async def ping_command(self, ctx: commands.Context):
        await self.ping_logic(ctx)

    @app_commands.command(name='ping', description="Check the bot's latency")
    async def ping_slash(self, interaction: discord.Interaction):
        await self.ping_logic(interaction)

    async def ping_logic(self, ctx):
        start_time = time.time()
        websocket_latency = round(self.bot.latency * 1000)

        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.from_rgb(43, 45, 49)
        )
        
        msg = await ctx.send(embed=embed) if isinstance(ctx, commands.Context) else await ctx.response.send_message(embed=embed, wait=True)
        
        round_trip = round((time.time() - start_time) * 1000)
        
        embed.description = f"**WebSocket:** {websocket_latency}ms\n**Round-trip:** {round_trip}ms"
        
        if isinstance(ctx, discord.Interaction):
            await ctx.edit_original_response(embed=embed)
        else:
            await msg.edit(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(CommonCommands(bot))