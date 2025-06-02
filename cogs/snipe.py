import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Dict, List
from collections import defaultdict

class Snipe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.deleted_messages: Dict[int, List[dict]] = defaultdict(list)
        self.edited_messages: Dict[int, List[dict]] = defaultdict(list)
        self.max_snipes = 10

    def _add_to_history(self, messages_dict: Dict[int, List[dict]], channel_id: int, message_data: dict):
        if len(messages_dict[channel_id]) >= self.max_snipes:
            messages_dict[channel_id].pop()
        messages_dict[channel_id].insert(0, message_data)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        message_data = {
            'content': message.content,
            'author': message.author,
            'time': datetime.now(),
            'attachments': [attachment.url for attachment in message.attachments],
            'reference': message.reference.message_id if message.reference else None
        }
        
        self._add_to_history(self.deleted_messages, message.channel.id, message_data)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return

        edit_data = {
            'before_content': before.content,
            'after_content': after.content,
            'author': before.author,
            'time': datetime.now()
        }
        
        self._add_to_history(self.edited_messages, before.channel.id, edit_data)

    @commands.hybrid_command(name="snipe")
    @app_commands.describe(index="The index of the deleted message to show (1-10)")
    async def snipe(self, ctx, index: int = 1):
        """Shows deleted messages. Use a number 1-10 to see older messages."""
        if not 1 <= index <= self.max_snipes:
            embed = discord.Embed(
                description=f"❌ Please provide a number between 1 and {self.max_snipes}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        channel = ctx.channel
        messages = self.deleted_messages.get(channel.id, [])

        if not messages or index > len(messages):
            embed = discord.Embed(
                description="❌ There are no recently deleted messages in this channel!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        message_data = messages[index - 1]
        
        embed = discord.Embed(color=0x2b2d31)  # Discord dark theme color
        
        author = message_data['author']
        embed.set_author(
            name=f"{author.name}'s Deleted Message",
            icon_url=author.avatar.url if author.avatar else author.default_avatar.url
        )

        # Main content section with emoji
        content = message_data['content'] or "No content"
        embed.description = f"📝 **Message Content**\n{content}"

        # Add attachment info if any
        if message_data['attachments']:
            attachment_list = "\n".join([f"• {url}" for url in message_data['attachments']])
            embed.add_field(
                name="📎 Attachments",
                value=attachment_list,
                inline=False
            )

        # Add reference info if it was a reply
        if message_data['reference']:
            embed.add_field(
                name="↩️ Reply Reference",
                value=f"Message ID: {message_data['reference']}",
                inline=False
            )

        # Timestamp in footer
        time_format = message_data['time'].strftime("%Y-%m-%d %H:%M:%S")
        embed.set_footer(
            text=f"#{channel.name} • {time_format} • Message {index}/{len(messages)}"
        )
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="editsnipe", aliases=["esnipe"])
    @app_commands.describe(index="The index of the edited message to show (1-10)")
    async def editsnipe(self, ctx, index: int = 1):
        """Shows edited messages. Use a number 1-10 to see older edits."""
        if not 1 <= index <= self.max_snipes:
            embed = discord.Embed(
                description=f"❌ Please provide a number between 1 and {self.max_snipes}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        channel = ctx.channel
        edits = self.edited_messages.get(channel.id, [])

        if not edits or index > len(edits):
            embed = discord.Embed(
                description="❌ There are no recently edited messages in this channel!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        edit_data = edits[index - 1]
        
        embed = discord.Embed(color=0x2b2d31)
        
        author = edit_data['author']
        embed.set_author(
            name=f"{author.name}'s Edited Message",
            icon_url=author.avatar.url if author.avatar else author.default_avatar.url
        )

        # Before and After content with emojis
        embed.add_field(
            name="📝 Original Message",
            value=edit_data['before_content'] or "No content",
            inline=False
        )
        embed.add_field(
            name="✏️ Edited Message",
            value=edit_data['after_content'] or "No content",
            inline=False
        )

        # Timestamp in footer
        time_format = edit_data['time'].strftime("%Y-%m-%d %H:%M:%S")
        embed.set_footer(
            text=f"#{channel.name} • {time_format} • Edit {index}/{len(edits)}"
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Snipe(bot))