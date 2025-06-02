import discord
from discord.ext import commands
from discord import app_commands
import time
from datetime import datetime

class StopwatchView(discord.ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id

    @discord.ui.button(label="Start/Stop", style=discord.ButtonStyle.primary)
    async def toggle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This is not your stopwatch!", ephemeral=True)
            return
            
        if self.user_id not in self.cog.stopwatches:
            # Start new stopwatch
            self.cog.stopwatches[self.user_id] = {
                'start_time': time.time(),
                'is_running': True,
                'laps': []
            }
            embed = discord.Embed(
                title="⏱️ Stopwatch Started",
                description="Timer has begun!",
                timestamp=datetime.utcnow()
            )
        else:
            stopwatch = self.cog.stopwatches[self.user_id]
            if stopwatch['is_running']:
                # Stop the stopwatch
                elapsed_time = time.time() - stopwatch['start_time']
                stopwatch['is_running'] = False
                stopwatch['elapsed_time'] = elapsed_time
                
                embed = discord.Embed(
                    title="⏹️ Stopwatch Stopped",
                    description=f"Time elapsed: `{self.cog._format_time(elapsed_time)}`",
                    timestamp=datetime.utcnow()
                )
                
                if stopwatch['laps']:
                    lap_text = "\n".join([f"Lap {i+1}: `{self.cog._format_time(lap)}`" 
                                        for i, lap in enumerate(stopwatch['laps'])])
                    embed.add_field(name="📋 Lap Times", value=lap_text)
            else:
                # Resume the stopwatch
                stopwatch['start_time'] = time.time() - stopwatch['elapsed_time']
                stopwatch['is_running'] = True
                embed = discord.Embed(
                    title="▶️ Stopwatch Resumed",
                    description="Timer is running!",
                    timestamp=datetime.utcnow()
                )

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Lap", style=discord.ButtonStyle.secondary)
    async def lap_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This is not your stopwatch!", ephemeral=True)
            return
            
        if self.user_id not in self.cog.stopwatches or not self.cog.stopwatches[self.user_id]['is_running']:
            embed = discord.Embed(
                title="⚠️ Error",
                description="No active stopwatch found!",
                timestamp=datetime.utcnow()
            )
        else:
            stopwatch = self.cog.stopwatches[self.user_id]
            current_time = time.time() - stopwatch['start_time']
            stopwatch['laps'].append(current_time)
            
            last_lap = stopwatch['laps'][-2] if len(stopwatch['laps']) > 1 else 0
            lap_difference = current_time - last_lap
            
            embed = discord.Embed(
                title="⏱️ Lap Recorded",
                description=f"Lap {len(stopwatch['laps'])}: `{self.cog._format_time(current_time)}`\n"
                           f"Lap Time: `{self.cog._format_time(lap_difference)}`",
                timestamp=datetime.utcnow()
            )

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Reset", style=discord.ButtonStyle.danger)
    async def reset_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This is not your stopwatch!", ephemeral=True)
            return
            
        if self.user_id in self.cog.stopwatches:
            del self.cog.stopwatches[self.user_id]
        
        embed = discord.Embed(
            title="🔄 Stopwatch Reset",
            description="Timer has been reset!",
            timestamp=datetime.utcnow()
        )
        await interaction.response.edit_message(embed=embed, view=self)

class Stopwatch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stopwatches = {}

    @commands.hybrid_command(
        name="stopwatch",
        description="Control your stopwatch",
        aliases=['sw']
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def stopwatch(self, ctx):
        """
        Control your stopwatch with buttons
        Usage: .stopwatch or /stopwatch
        """
        try:
            user_id = str(ctx.author.id)
            
            if user_id not in self.stopwatches:
                embed = discord.Embed(
                    title="⏱️ Stopwatch",
                    description="Click the buttons below to control your stopwatch!",
                    timestamp=datetime.utcnow()
                )
            else:
                stopwatch = self.stopwatches[user_id]
                current_time = time.time() - stopwatch['start_time'] if stopwatch['is_running'] else stopwatch['elapsed_time']
                
                embed = discord.Embed(
                    title=f"⏱️ Stopwatch {'Running' if stopwatch['is_running'] else 'Stopped'}",
                    description=f"Current time: `{self._format_time(current_time)}`",
                    timestamp=datetime.utcnow()
                )
                
                if stopwatch['laps']:
                    lap_text = "\n".join([f"Lap {i+1}: `{self._format_time(lap)}`" 
                                        for i, lap in enumerate(stopwatch['laps'])])
                    embed.add_field(name="📋 Lap Times", value=lap_text)

            view = StopwatchView(self, user_id)
            await ctx.send(embed=embed, view=view)

        except Exception as e:
            embed = discord.Embed(
                title="⚠️ Error",
                description=f"An error occurred: {str(e)}",
                timestamp=datetime.utcnow()
            )
            await ctx.send(embed=embed)

    def _format_time(self, seconds):
        """Format seconds into readable time"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:05.2f}"
        return f"{minutes:02d}:{seconds:05.2f}"

    @stopwatch.error
    async def command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            seconds = round(error.retry_after)
            embed = discord.Embed(
                title="⚠️ Cooldown",
                description=f"Please wait `{seconds}` seconds before using this command again.",
                timestamp=datetime.utcnow()
            )
        else:
            embed = discord.Embed(
                title="⚠️ Error",
                description=f"An error occurred: {str(error)}",
                timestamp=datetime.utcnow()
            )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Stopwatch(bot))