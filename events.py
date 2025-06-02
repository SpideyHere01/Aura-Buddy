import discord
from discord.ext import commands

async def on_guild_join(guild):
    print(f"Bot has joined a new guild: {guild.name} (ID: {guild.id})")
    print(f"Guild owner: {guild.owner.name} (ID: {guild.owner.id})")
    print(f"Total members: {guild.member_count}")
    # Log channel for bot events
    log_channel_id = 1303757449152434227  # Replace with your actual log channel ID
    log_channel = guild.get_channel(log_channel_id)
    
    if log_channel:
        embed = discord.Embed(
            title="New Guild Joined",
            description=f"Bot has joined a new guild!",
            color=discord.Color.green()
        )
        embed.add_field(name="Guild Name", value=guild.name, inline=True)
        embed.add_field(name="Guild ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=f"{guild.owner.name} ({guild.owner.id})", inline=False)
        embed.add_field(name="Member Count", value=guild.member_count, inline=True)
        
        await log_channel.send(embed=embed)
