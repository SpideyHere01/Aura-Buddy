import discord
from discord.ext import commands
import asyncio
from typing import Dict, Optional

class Lafda(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_lafdas = {}  # Store active arguments

    class LafdaSession:
        def __init__(self, user1: discord.Member, user2: discord.Member, channel: discord.TextChannel, starter: discord.Member, duration: Optional[int] = None):
            self.user1 = user1
            self.user2 = user2
            self.channel = channel
            self.starter = starter  # Store who started the lafda
            self.message_votes = {}
            self.start_time = asyncio.get_event_loop().time()
            self.last_activity = asyncio.get_event_loop().time()  # Track last activity
            self.total_messages = 0
            self.duration = duration  # Store the duration in minutes if specified
            self.timer_task = None  # Store the timer task
            self.inactivity_task = None  # New task for tracking inactivity

    @commands.command(name="lafda")
    @commands.guild_only()
    @commands.cooldown(1, 30, commands.BucketType.channel)  # One lafda per channel every 30 seconds
    async def start_lafda(self, ctx, user1: discord.Member = None, user2: discord.Member = None, *, duration: str = None):
        """Start a lafda (argument) between two users with optional duration (t<minutes>)"""
        try:
            if user1 is None or user2 is None:
                embed = discord.Embed(
                    description="❌ Please mention two users to start a lafda!\nUsage: `.lafda @user1 @user2 [t<minutes>]`",
                    color=discord.Color.from_rgb(43, 45, 49)
                )
                await ctx.send(embed=embed)
                return

            if ctx.channel.id in self.active_lafdas:
                embed = discord.Embed(
                    description="❌ A lafda is already active in this channel!",
                    color=discord.Color.from_rgb(43, 45, 49)
                )
                await ctx.send(embed=embed)
                return

            # Parse duration if provided
            time_duration = None
            if duration:
                if duration.startswith('t'):
                    try:
                        time_duration = int(duration[1:])
                        if time_duration <= 0:
                            raise ValueError
                        if time_duration > 60:  # Maximum 1 hour
                            embed = discord.Embed(
                                description="❌ Maximum lafda duration is 60 minutes!",
                                color=discord.Color.from_rgb(43, 45, 49)
                            )
                            await ctx.send(embed=embed)
                            return
                    except ValueError:
                        embed = discord.Embed(
                            description="❌ Invalid time format! Use t<minutes> (e.g., t5 for 5 minutes)",
                            color=discord.Color.from_rgb(43, 45, 49)
                        )
                        await ctx.send(embed=embed)
                        return

            if user1.bot or user2.bot:
                embed = discord.Embed(
                    description="❌ Bots cannot participate in lafdas!",
                    color=discord.Color.from_rgb(43, 45, 49)
                )
                await ctx.send(embed=embed)
                return

            if user1 == user2:
                embed = discord.Embed(
                    description="❌ A user cannot have a lafda with themselves!",
                    color=discord.Color.from_rgb(43, 45, 49)
                )
                await ctx.send(embed=embed)
                return

            session = self.LafdaSession(user1, user2, ctx.channel, ctx.author, time_duration)
            self.active_lafdas[ctx.channel.id] = session

            # Start both timer tasks
            if time_duration:
                session.timer_task = asyncio.create_task(self.auto_stop_lafda(ctx.channel.id, time_duration * 60))
            session.inactivity_task = asyncio.create_task(self.check_inactivity(ctx.channel.id))
            
            duration_text = f"\n⏱️ Time limit: {time_duration} minutes" if time_duration else ""
            
            embed = discord.Embed(
                title="🔥 New Lafda Started!",
                description=(
                    f"A heated debate has begun between {user1.mention} and {user2.mention}!\n\n"
                    "**Guidelines:**\n"
                    "• Only messages from these two users will be counted\n"
                    "• React with 🔥 to vote for messages you agree with\n"
                    "• Use `.stoplafda` to end the debate and count votes"
                    f"{duration_text}"
                ),
                color=discord.Color.from_rgb(43, 45, 49)
            )
            embed.set_footer(text="May the best debater win!")
            
            await ctx.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                description=f"❌ An error occurred: {str(e)}",
                color=discord.Color.from_rgb(43, 45, 49)
            )
            await ctx.send(embed=embed)

    @start_lafda.error
    async def lafda_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                description=f"❌ Please wait {int(error.retry_after)} seconds before starting another lafda!",
                color=discord.Color.from_rgb(43, 45, 49)
            )
            await ctx.send(embed=embed)

    @commands.command(name="stoplafda")
    @commands.guild_only()
    async def stop_lafda(self, ctx, *, auto_stopped: bool = False):
        """Stop the active lafda and declare the winner"""
        try:
            if ctx.channel.id not in self.active_lafdas:
                embed = discord.Embed(
                    description="❌ No active lafda in this channel!",
                    color=discord.Color.from_rgb(43, 45, 49)
                )
                await ctx.send(embed=embed)
                return

            session = self.active_lafdas[ctx.channel.id]
            
            # Check if the user has permission to stop the lafda
            if not auto_stopped and ctx.author != session.starter and not ctx.author.guild_permissions.administrator:
                embed = discord.Embed(
                    description="❌ Only the person who started the lafda or an admin can stop it!",
                    color=discord.Color.from_rgb(43, 45, 49)
                )
                await ctx.send(embed=embed)
                return

            # Cancel both timer tasks if they exist
            if session.timer_task:
                session.timer_task.cancel()
            if session.inactivity_task:
                session.inactivity_task.cancel()

            # Calculate votes
            user1_votes = sum(votes['count'] for votes in session.message_votes.values() 
                            if votes['author'] == session.user1.id)
            user2_votes = sum(votes['count'] for votes in session.message_votes.values() 
                            if votes['author'] == session.user2.id)

            # Calculate duration
            duration = int(asyncio.get_event_loop().time() - session.start_time)
            minutes = duration // 60
            seconds = duration % 60

            embed = discord.Embed(
                title="🏆 Lafda Results",
                color=discord.Color.from_rgb(43, 45, 49)
            )

            # Calculate messages per user
            user1_messages = sum(1 for votes in session.message_votes.values() 
                                if votes['author'] == session.user1.id)
            user2_messages = sum(1 for votes in session.message_votes.values() 
                                if votes['author'] == session.user2.id)

            # Stats fields with messages count
            embed.add_field(
                name=f"{session.user1.display_name}",
                value=f"🔥 **{user1_votes}** votes\n💭 **{user1_messages}** messages",
                inline=True
            )
            embed.add_field(
                name=f"{session.user2.display_name}",
                value=f"🔥 **{user2_votes}** votes\n💭 **{user2_messages}** messages",
                inline=True
            )
            
            embed.add_field(
                name="Duration",
                value=f"⏱️ {minutes}m {seconds}s\n📊 Total Messages: **{session.total_messages}**",
                inline=False
            )

            # Determine winner
            if user1_votes > user2_votes:
                winner = session.user1
                winner_votes = user1_votes
                embed.description = f"🎉 **{winner.mention} wins the debate!**\nVictory achieved with **{winner_votes}** votes"
            elif user2_votes > user1_votes:
                winner = session.user2
                winner_votes = user2_votes
                embed.description = f"🎉 **{winner.mention} wins the debate!**\nVictory achieved with **{winner_votes}** votes"
            else:
                embed.description = "🤝 **It's a tie!** Both users received equal votes!"

            embed.set_footer(text="Thanks for participating!")
            await ctx.send(embed=embed)
            del self.active_lafdas[ctx.channel.id]

        except Exception as e:
            embed = discord.Embed(
                description=f"❌ An error occurred: {str(e)}",
                color=discord.Color.from_rgb(43, 45, 49)
            )
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        try:
            channel_id = message.channel.id
            if channel_id not in self.active_lafdas:
                return

            session = self.active_lafdas[channel_id]
            if message.author.id not in [session.user1.id, session.user2.id]:
                return

            # Update last activity time
            session.last_activity = asyncio.get_event_loop().time()

            # Initialize vote tracking for this message
            session.message_votes[message.id] = {
                'author': message.author.id,
                'count': 0
            }

            # Update total message counter and send "Me na sehta" every 6 combined messages
            session.total_messages += 1
            if session.total_messages % 6 == 0:  # Will trigger every 6 messages regardless of which user sent them
                await message.channel.send("Me na sehta! 🗣️")

            # Add fire reaction for voting
            await message.add_reaction("🔥")

        except Exception as e:
            print(f"Error in on_message: {str(e)}")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        try:
            channel_id = reaction.message.channel.id
            if channel_id not in self.active_lafdas:
                return

            session = self.active_lafdas[channel_id]
            if reaction.message.id not in session.message_votes:
                return

            if str(reaction.emoji) == "🔥":
                session.message_votes[reaction.message.id]['count'] += 1

        except Exception as e:
            print(f"Error in on_reaction_add: {str(e)}")

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if user.bot:
            return

        try:
            channel_id = reaction.message.channel.id
            if channel_id not in self.active_lafdas:
                return

            session = self.active_lafdas[channel_id]
            if reaction.message.id not in session.message_votes:
                return

            if str(reaction.emoji) == "🔥":
                session.message_votes[reaction.message.id]['count'] -= 1

        except Exception as e:
            print(f"Error in on_reaction_remove: {str(e)}")

    async def auto_stop_lafda(self, channel_id: int, duration: int):
        """Auto-stop the lafda after the specified duration"""
        # Send warning 1 minute before ending
        await asyncio.sleep(duration - 60)  # Sleep for duration minus 1 minute
        if channel_id in self.active_lafdas:
            channel = self.active_lafdas[channel_id].channel
            warning_embed = discord.Embed(
                description="⚠️ One minute remaining in the lafda!",
                color=discord.Color.from_rgb(43, 45, 49)
            )
            await channel.send(embed=warning_embed)
        
        # Wait the final minute
        await asyncio.sleep(60)
        if channel_id in self.active_lafdas:
            channel = self.active_lafdas[channel_id].channel
            ctx = await self.bot.get_context(await channel.fetch_message(channel.last_message_id))
            await self.stop_lafda(ctx, auto_stopped=True)

    async def check_inactivity(self, channel_id: int):
        """Check for lafda inactivity and auto-stop if inactive for 5 minutes"""
        while True:
            await asyncio.sleep(30)  # Check every 30 seconds
            if channel_id not in self.active_lafdas:
                break
            
            session = self.active_lafdas[channel_id]
            current_time = asyncio.get_event_loop().time()
            inactive_duration = current_time - session.last_activity
            
            if inactive_duration >= 300:  # 5 minutes = 300 seconds
                channel = session.channel
                ctx = await self.bot.get_context(await channel.fetch_message(channel.last_message_id))
                
                # Send inactivity warning
                warning_embed = discord.Embed(
                    description="⚠️ Lafda ended due to 5 minutes of inactivity!",
                    color=discord.Color.from_rgb(43, 45, 49)
                )
                await channel.send(embed=warning_embed)
                
                await self.stop_lafda(ctx, auto_stopped=True)
                break

async def setup(bot):
    await bot.add_cog(Lafda(bot)) 