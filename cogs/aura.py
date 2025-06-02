import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime
from db.mongo import aura_points_collection
import motor
from pymongo import ReturnDocument

class AuraCog(commands.Cog, name="Aura"):
    THUMBS_UP_VALUE = 100
    THUMBS_DOWN_VALUE = -50
    VOTE_DURATION = 30  # seconds
    
    def __init__(self, bot):
        self.bot = bot
        self.active_votes = {}
        self.LOG_CHANNEL_ID = 1290705365671088211  # Ensure this ID is correct and the bot has access
        
    def load_aura_points(self):
        # Removed: Use MongoDB instead
        pass

    def save_aura_points(self):
        # Removed: Use MongoDB instead
        pass

    @commands.cooldown(1, 300, commands.BucketType.user)
    @commands.command(name='aura', help="Request aura points for a message")
    async def aura_command(self, ctx):
        await self.aura_logic(ctx)

    @app_commands.checks.cooldown(1, 300)
    @app_commands.command(name='aura', description="Request aura points for a message")
    async def aura_slash(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        if not interaction.message or not interaction.message.reference:
            await interaction.followup.send(
                embed=discord.Embed(
                    description="❌ Please use this command as a reply to the message you want to give aura points for.",
                    color=discord.Color.from_rgb(43, 45, 49)
                )
            )
            return
            
        try:
            await self.aura_logic(interaction)
        except Exception as e:
            print(f"Slash command error: {type(e).__name__}: {str(e)}")
            # Don't send any error message here since aura_logic handles its own errors

    @aura_slash.error
    async def aura_slash_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            remaining_time = int(error.retry_after)
            minutes = remaining_time // 60
            seconds = remaining_time % 60
            
            time_format = []
            if minutes > 0:
                time_format.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
            if seconds > 0:
                time_format.append(f"{seconds} second{'s' if seconds != 1 else ''}")
            
            try:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        description=f"⏳ This command is on cooldown. Please wait {' and '.join(time_format)} before trying again.",
                        color=discord.Color.from_rgb(43, 45, 49)
                    )
                )
            except:
                await interaction.followup.send(
                    embed=discord.Embed(
                        description=f"⏳ This command is on cooldown. Please wait {' and '.join(time_format)} before trying again.",
                        color=discord.Color.from_rgb(43, 45, 49)
                    )
                )

    async def aura_logic(self, ctx):
        print("Starting aura_logic")  # Debug statement
        channel_id = ctx.channel.id
        
        if (channel_id in self.active_votes and self.active_votes[channel_id]):
            error_embed = discord.Embed(
                title="Vote in Progress",
                description="There's already an active aura vote in this channel. Please wait for the current vote to finish before starting a new one.",
                color=discord.Color.from_rgb(43, 45, 49)
            )
            error_embed.set_footer(text="Try again in a few seconds")
            print("Vote in progress")  # Debug statement
            await self.send_response(ctx, embed=error_embed)
            return
        
        self.active_votes[channel_id] = True
        print("Vote initiated")  # Debug statement
        
        try:
            message_reference = ctx.message.reference if isinstance(ctx, commands.Context) else getattr(ctx.message, 'reference', None)

            if not message_reference:
                error_embed = discord.Embed(
                    description="❌ Please use this command as a reply to the message you want to give aura points for.",
                    color=discord.Color.from_rgb(43, 45, 49)
                )
                print("No message reference found")  # Debug statement
                await self.send_response(ctx, embed=error_embed)
                self.active_votes[channel_id] = False
                return

            try:
                referenced_message = await asyncio.wait_for(
                    ctx.channel.fetch_message(message_reference.message_id),
                    timeout=5.0
                )
                print("Referenced message fetched")  # Debug statement
            except asyncio.TimeoutError:
                error_embed = discord.Embed(
                    description="⚠️ The server is responding slowly. Please try again in a few moments.",
                    color=discord.Color.from_rgb(43, 45, 49)
                )
                print("Timeout while fetching message")  # Debug statement
                await self.send_response(ctx, embed=error_embed)
                self.active_votes[channel_id] = False
                return
            
            referenced_author = referenced_message.author
            
            if referenced_message.author.id == ctx.author.id:
                error_embed = discord.Embed(
                    description="❌ You cannot give aura points to yourself!",
                    color=discord.Color.from_rgb(43, 45, 49)
                )
                print("User attempted to give aura to themselves")  # Debug statement
                await self.send_response(ctx, embed=error_embed)
                self.active_votes[channel_id] = False
                return

            await referenced_message.add_reaction('👍')
            await referenced_message.add_reaction('👎')
            print("Reactions added to the message")  # Debug statement
            
            vote_embed = discord.Embed(
                description=f"💫 {ctx.author.mention} requested aura points for {referenced_author.mention}\n\nReact with 👍 or 👎 to vote!",
                color=discord.Color.from_rgb(43, 45, 49)
            )
            vote_embed.set_thumbnail(url="https://images-ext-1.discordapp.net/external/KYFTcv_uS_8bN3IzAi8pzDChekYecFS_m8M-6d26zk0/https/media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif?width=462&height=260")
            
            await self.send_response(ctx, embed=vote_embed)
            
            await asyncio.sleep(self.VOTE_DURATION)
            print("Vote duration completed")  # Debug statement
            
            referenced_message = await ctx.channel.fetch_message(message_reference.message_id)
            
            thumbs_up_count = 0
            thumbs_down_count = 0
            for reaction in referenced_message.reactions:
                if str(reaction.emoji) == '👍':
                    thumbs_up_count = reaction.count - 1
                elif str(reaction.emoji) == '👎':
                    thumbs_down_count = reaction.count - 1
            
            aura_count = (thumbs_up_count * self.THUMBS_UP_VALUE) + (thumbs_down_count * self.THUMBS_DOWN_VALUE)
            author_id = str(referenced_author.id)
            
            # Use $inc to increment aura points and retrieve updated document
            update_result = await aura_points_collection.find_one_and_update(
                {"user_id": author_id},
                {"$inc": {"points": aura_count}},
                return_document=ReturnDocument.AFTER  # Ensure correct import
            )
            new_points = update_result['points'] if update_result else aura_count
            
            if aura_count < 0:
                # Optionally handle negative points
                pass

            log_channel = self.bot.get_channel(self.LOG_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    description=f"👤 **User:** {referenced_author.mention}\n💫 **Aura Change:** `{aura_count:,}` points\n📊 **New Balance:** `{new_points:,}` points",
                    color=discord.Color.from_rgb(43, 45, 49),
                    timestamp=datetime.utcnow()
                )
                await log_channel.send(embed=log_embed)
                print("Log embed sent")  # Debug statement

            result_embed = discord.Embed(
                description=f"✨ {referenced_author.mention} received **{aura_count}** aura points! (Total: **{new_points}**)",
                color=discord.Color.from_rgb(43, 45, 49)
            )
            await self.send_response(ctx, embed=result_embed)
            
        except discord.NotFound:
            error_embed = discord.Embed(
                description="❌ I couldn't find the message you replied to. It might have been deleted.",
                color=discord.Color.from_rgb(43, 45, 49)
            )
            print("Referenced message not found")  # Debug statement
            await self.send_response(ctx, embed=error_embed)
        except discord.Forbidden:
            error_embed = discord.Embed(
                description="❌ I don't have the required permissions. Please make sure I can:\n• Add reactions\n• Read message history\n• Send messages",
                color=discord.Color.from_rgb(43, 45, 49)
            )
            print("Insufficient permissions")  # Debug statement
            await self.send_response(ctx, embed=error_embed)
        except discord.HTTPException as e:
            error_embed = discord.Embed(
                description="⚠️ Unable to process your request due to Discord API limitations. Please try again in a few moments.",
                color=discord.Color.from_rgb(43, 45, 49)
            )
            print(f"HTTP Exception in aura command: {e}")  # Debug statement
            await self.send_response(ctx, embed=error_embed)
            print(f"HTTP Exception in aura command: {e}")
        except Exception as e:
            error_embed = discord.Embed(
                description="⚠️ Unable to process your request at this time. Please ensure you're using the command correctly.",
                color=discord.Color.from_rgb(43, 45, 49)
            )
            print(f"Error in aura command: {type(e).__name__}: {str(e)}")  # Debug statement
            await self.send_response(ctx, embed=error_embed)
            print(f"Error in aura command: {type(e).__name__}: {str(e)}")
        finally:
            self.active_votes[channel_id] = False
            print("Vote flag reset")  # Debug statement

    async def send_response(self, ctx, content=None, embed=None):
        if isinstance(ctx, discord.Interaction):
            if ctx.response.is_done():
                await ctx.followup.send(content=content, embed=embed)
            else:
                await ctx.response.send_message(content=content, embed=embed)
        else:
            await ctx.send(content=content, embed=embed)

async def setup(bot):
    await bot.add_cog(AuraCog(bot))