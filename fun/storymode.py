import discord
from discord.ext import commands
import json
import random
from typing import Dict, List, Optional
import asyncio
import google.generativeai as genai
import os
from dotenv import load_dotenv
import traceback

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

class Story:
    def __init__(self, story_id: str, title: str, data: dict):
        self.story_id = story_id
        self.title = title
        self.nodes = data['nodes']
        self.start_node = data['start_node']
        self.rewards = data.get('rewards', {})

class StorySession:
    def __init__(self, story: Story, user_id: int):
        self.story = story
        self.user_id = user_id
        self.current_node = story.start_node
        self.choices_made = []
        self.is_active = True

class StoryMode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_sessions: Dict[int, StorySession] = {}
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            print("Warning: GEMINI_API_KEY not found")
            self.model = None

    @commands.group(name="story", invoke_without_command=True)
    async def story(self, ctx):
        """Main story command"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="📖 Story Mode",
                description="Interactive Story Experience",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Commands",
                value=(
                    "`!story generate [theme]` - New story\n"
                    "`!story continue` - Continue story\n"
                    "`!story quit` - End story"
                ),
                inline=False
            )
            try:
                await ctx.send(embed=embed)
            except discord.HTTPException as e:
                print(f"Failed to send help message: {e}")
                await ctx.send("Type `!story generate` to start a new story!")

    @story.command(name="generate")
    @commands.cooldown(1, 5, commands.BucketType.user)  # Add cooldown
    async def generate_new_story(self, ctx, *, theme: str = None):
        """Generate a new story"""
        try:
            if ctx.author.id in self.active_sessions:
                await ctx.send("You have an active story! Use `!story continue` or `!story quit`")
                return

            async with ctx.typing():
                story_data = await self.generate_simple_story(theme)
                
                if not story_data:
                    await ctx.send("❌ Failed to generate story. Please try again!")
                    return

                story = Story(
                    story_id=f"gen_{random.randint(1000, 9999)}",
                    title=story_data['title'],
                    data=story_data
                )
                
                session = StorySession(story, ctx.author.id)
                self.active_sessions[ctx.author.id] = session

                await self.display_story_node(ctx, session)

        except commands.CommandOnCooldown as e:
            await ctx.send(f"Please wait {e.retry_after:.1f}s before generating another story.")
        except Exception as e:
            print(f"Error in generate_new_story: {e}")
            await ctx.send("An error occurred. Please try again later.")

    async def generate_simple_story(self, theme: str = None) -> dict:
        """Generate a theme-specific story structure"""
        try:
            theme = theme.strip().lower() if theme else "adventure"
            
            # Special story template for Valorant-related themes
            if "valorant" in theme:
                return {
                    "title": "Valorant Ranked Adventure",
                    "start_node": "start",
                    "nodes": {
                        "start": {
                            "text": "You're about to start your Valorant ranked journey. Your current rank is Iron, but you know you deserve better. What's your approach?",
                            "choices": {
                                "1": {"text": "Create a new account to smurf", "next": "smurf_choice"},
                                "2": {"text": "Grind on main account", "next": "main_account"}
                            }
                        },
                        "smurf_choice": {
                            "text": "You've created a new account. In your first placement match, you're clearly better than others. What do you do?",
                            "choices": {
                                "1": {"text": "Show off your skills and dominate", "next": "dominate"},
                                "2": {"text": "Play casually and have fun", "next": "casual_play"}
                            }
                        },
                        "main_account": {
                            "text": "You decide to face the challenge on your main account. The games are tough but fair.",
                            "choices": {
                                "1": {"text": "Keep practicing and improving", "next": "improvement"},
                                "2": {"text": "Reconsider smurfing", "next": "temptation"}
                            }
                        },
                        "dominate": {
                            "text": "Your aggressive playstyle ruins the experience for new players. Some report you for smurfing.",
                            "choices": {
                                "1": {"text": "Continue anyway", "next": "bad_ending"}
                            }
                        },
                        "casual_play": {
                            "text": "You play at a moderate level, having fun while not ruining others' experience.",
                            "choices": {
                                "1": {"text": "Return to main account", "next": "redemption"}
                            }
                        },
                        "improvement": {
                            "text": "Through dedication and practice, you naturally improve and rank up!",
                            "choices": {
                                "1": {"text": "Celebrate your achievement", "next": "good_ending"}
                            }
                        },
                        "temptation": {
                            "text": "The grind is tough, but taking shortcuts won't make you a better player.",
                            "choices": {
                                "1": {"text": "Accept the challenge", "next": "good_ending"}
                            }
                        },
                        "bad_ending": {
                            "text": "Your account gets banned for smurfing. Maybe it's better to play fair next time.",
                            "choices": {},
                            "ending": True
                        },
                        "redemption": {
                            "text": "You realize fair play is more rewarding. You return to your main account with new insights.",
                            "choices": {},
                            "ending": True
                        },
                        "good_ending": {
                            "text": "Through legitimate practice and dedication, you achieve your desired rank! True improvement feels rewarding.",
                            "choices": {},
                            "ending": True
                        }
                    },
                    "rewards": {
                        "completion": {"aura_points": 25},
                        "special_endings": {
                            "bad_ending": {"aura_points": 10, "role": "Lesson Learned"},
                            "redemption": {"aura_points": 75, "role": "Fair Player"},
                            "good_ending": {"aura_points": 100, "role": "True Champion"}
                        }
                    }
                }
            
            # Add more theme-specific templates here
            elif "mystery" in theme:
                # Mystery story template
                pass
            elif "fantasy" in theme:
                # Fantasy story template
                pass
            else:
                # Default story template
                return {
                    "title": f"{theme.title()} Adventure",
                    "start_node": "start",
                    "nodes": {
                        "start": {
                            "text": f"You begin your journey into {theme}. The path ahead looks challenging but exciting.",
                            "choices": {
                                "1": {"text": "Take the strategic approach", "next": "strategic"},
                                "2": {"text": "Go for aggressive plays", "next": "aggressive"}
                            }
                        },
                        "strategic": {
                            "text": "You chose the strategic approach. The path ahead looks challenging but exciting.",
                            "choices": {
                                "1": {"text": "Continue", "next": "strategic_end"}
                            }
                        },
                        "aggressive": {
                            "text": "You chose the aggressive approach. The path ahead looks challenging but exciting.",
                            "choices": {
                                "1": {"text": "Continue", "next": "aggressive_end"}
                            }
                        },
                        "strategic_end": {
                            "text": "You completed your journey strategically!",
                            "choices": {},
                            "ending": True
                        },
                        "aggressive_end": {
                            "text": "You completed your journey aggressively!",
                            "choices": {},
                            "ending": True
                        }
                    },
                    "rewards": {
                        "completion": {"aura_points": 25},
                        "special_endings": {
                            "strategic_end": {"aura_points": 50},
                            "aggressive_end": {"aura_points": 100}
                        }
                    }
                }

        except Exception as e:
            print(f"Error generating story: {e}")
            return None

    async def display_story_node(self, ctx, session: StorySession):
        """Display story node and handle choices"""
        try:
            node = session.story.nodes[session.current_node]
            
            embed = discord.Embed(
                title=session.story.title,
                description=node["text"],
                color=discord.Color.blue()
            )

            if node.get("choices"):
                choices_text = "\n".join(
                    f"{num}. {choice['text']}" 
                    for num, choice in node["choices"].items()
                )
                embed.add_field(name="Choices", value=choices_text, inline=False)
                
                try:
                    message = await ctx.send(embed=embed)
                    
                    def check(m):
                        return (
                            m.author.id == session.user_id and 
                            m.channel.id == ctx.channel.id and 
                            m.content in node["choices"]
                        )

                    choice_msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                    choice = node["choices"][choice_msg.content]
                    session.current_node = choice["next"]
                    await self.display_story_node(ctx, session)

                except asyncio.TimeoutError:
                    await ctx.send("Story timeout! Use `!story continue` to resume.")
                except discord.HTTPException as e:
                    print(f"Discord API error: {e}")
                    await ctx.send("There was an error displaying the story. Please try again.")

            elif node.get("ending", False):
                embed.add_field(name="🏁 The End", value="Story Complete!", inline=False)
                try:
                    await ctx.send(embed=embed)
                except discord.HTTPException:
                    await ctx.send("Story complete! Thanks for playing!")
                del self.active_sessions[session.user_id]

        except Exception as e:
            print(f"Error in display_story_node: {e}")
            await ctx.send("An error occurred. Use `!story quit` to reset.")

    @story.command(name="quit")
    async def quit_story(self, ctx):
        """Quit current story"""
        if ctx.author.id in self.active_sessions:
            del self.active_sessions[ctx.author.id]
            await ctx.send("Story ended. Use `!story generate` to start a new one!")
        else:
            await ctx.send("You don't have an active story!")

    @story.command(name="continue")
    async def continue_story(self, ctx):
        """Continue current story"""
        if ctx.author.id in self.active_sessions:
            await self.display_story_node(ctx, self.active_sessions[ctx.author.id])
        else:
            await ctx.send("No active story! Use `!story generate` to start one.")

async def setup(bot):
    await bot.add_cog(StoryMode(bot)) 