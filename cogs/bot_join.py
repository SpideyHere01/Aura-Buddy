import discord
from discord.ext import commands

class BotJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        # Send DM to the person who added the bot
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.bot_add, limit=1):
                if entry.target.id == self.bot.user.id:
                    user = entry.user
                    # DM Embed with improved design
                    dm_embed = discord.Embed(
                        title="🎉 Thank you for adding me!",
                        description="I'm excited to help enhance your Discord experience!",
                        timestamp=discord.utils.utcnow()
                    )
                    
                    dm_embed.set_thumbnail(url=self.bot.user.display_avatar.url)
                    
                    prefix = "."
                    dm_embed.add_field(
                        name="📝 Getting Started",
                        value=f"• Prefix: `{prefix}`\n"
                              f"• Type `{prefix}help` to see all commands\n"
                              f"• Join our community for support & updates",
                        inline=False
                    )
                    
                    dm_embed.add_field(
                        name="🔗 Quick Links",
                        value="• [Support Server](https://discord.gg/jCRgRPC7Ah)\n"
                              "• [Invite Bot](https://discord.com/api/oauth2/authorize)",
                        inline=False
                    )
                    
                    dm_embed.set_footer(text=f"Added to: {guild.name}", icon_url=guild.icon.url if guild.icon else None)
                    
                    # DM View with Support button
                    class DMButtons(discord.ui.View):
                        def __init__(self):
                            super().__init__(timeout=None)
                            support_button = discord.ui.Button(
                                label="🏠 Support Server",
                                url="https://discord.gg/jCRgRPC7Ah",
                                style=discord.ButtonStyle.gray
                            )
                            self.add_item(support_button)
                    
                    try:
                        await user.send(embed=dm_embed, view=DMButtons())
                    except discord.Forbidden:
                        print(f"Couldn't DM user {user.name}")
                    break
        except discord.Forbidden:
            print(f"No access to audit logs in {guild.name}")
        
        # Find the first suitable channel
        channel = discord.utils.get(guild.text_channels, name='bot-commands') or \
                 discord.utils.get(guild.text_channels, name='general') or \
                 guild.text_channels[0]
        
        # Create server welcome embed with improved design
        server_embed = discord.Embed(
            title="👋 Hello Everyone!",
            description="Thank you for adding me to your server! I'm Aura Buddy, your new server companion.",
            timestamp=discord.utils.utcnow()
        )
        
        server_embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        server_embed.add_field(
            name="🚀 Quick Start",
            value=f"• Use `.help` to discover all features\n"
                  f"• Need help? Join our community below!",
            inline=False
        )
        
        server_embed.set_footer(text="Type .help to get started!")
        
        # Create button view for server message
        class ServerButtons(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)
                support_button = discord.ui.Button(
                    label="🏠 Support Server",
                    url="https://discord.gg/jCRgRPC7Ah",
                    style=discord.ButtonStyle.gray
                )
                self.add_item(support_button)
        
        try:
            # Try to send with button first
            try:
                await channel.send(embed=server_embed, view=ServerButtons())
            except discord.HTTPException:
                # If button fails (no link perms), send without button
                server_embed.add_field(
                    name="🔗 Support Server",
                    value="https://discord.gg/jCRgRPC7Ah",
                    inline=False
                )
                await channel.send(embed=server_embed)
        except discord.Forbidden:
            print(f"Failed to send welcome message in {guild.name}")

async def setup(bot):
    await bot.add_cog(BotJoin(bot)) 