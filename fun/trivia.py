import google.generativeai as genai
import random
import json
import asyncio
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from discord.ext import commands
import discord
from discord.ui import Button, View
import logging

# Load environment variables
load_dotenv()

# At the top of the file, add logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TriviaGame:
    def __init__(self):
        # Initialize Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            raise ValueError("GEMINI_API_KEY not found in environment variables")
            
        logger.info(f"API key loaded: {'*' * (len(api_key)-4)}{api_key[-4:]}")
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            response = self.model.generate_content("Say 'OK' if you can receive this message.")
            logger.info(f"API test response: {response.text if response else 'No response'}")
        except Exception as e:
            logger.error(f"Error initializing Gemini API: {str(e)}")
            raise
        
        # Game settings
        self.DEFAULT_TIMER = 10  # seconds
        self.MAX_QUESTIONS = 10
        
        # Available categories
        self.categories = [
            "General Knowledge", "Gaming", "Anime", "Memes", 
            "Science", "History", "Geography", "Movies",
            "Technology", "Sports", "Music", "Literature"
        ]
        
        # Store active games
        self.current_games: Dict[int, Dict] = {}
        
        # Add after other initialization code
        self.last_api_call = None
        self.MIN_API_INTERVAL = 1  # Minimum seconds between API calls
        
        # Add to initialization
        self.question_cache = {}  # category -> list of questions
        self.cache_size = 5  # questions to cache per category

    def sanitize_input(self, text: str) -> str:
        """Sanitize user input to prevent injection attacks"""
        return text.strip().replace('{', '').replace('}', '')
    
    async def generate_question(self, category: str) -> Dict:
        """Generate a trivia question using Gemini API"""
        category = self.sanitize_input(category)
        if category not in self.categories:
            logger.warning(f"Invalid category attempted: {category}")
            return None
        
        if self.last_api_call:
            time_since_last = (datetime.now() - self.last_api_call).total_seconds()
            if time_since_last < self.MIN_API_INTERVAL:
                await asyncio.sleep(self.MIN_API_INTERVAL - time_since_last)
        
        self.last_api_call = datetime.now()
        
        prompt = f"""Generate a multiple choice trivia question about {category}.
        Format your response as a JSON object like this:
        {{
            "question": "What is the capital of France?",
            "options": ["Paris", "London", "Berlin", "Madrid"],
            "correct_answer": "Paris",
            "explanation": "Paris is the capital city of France",
            "difficulty": "easy"
        }}"""
        
        try:
            logger.info(f"Attempting to generate question for category: {category}")
            response = self.model.generate_content(prompt)
            
            if not response or not response.text:
                logger.info("Received empty response from API")
                return None
            
            logger.info(f"Raw API response: {response.text}")
            
            # Clean the response text
            cleaned_text = response.text.strip()
            # Remove any markdown code block markers if present
            cleaned_text = cleaned_text.replace('```json', '').replace('```', '').strip()
            
            try:
                question_data = json.loads(cleaned_text)
            except json.JSONDecodeError as je:
                logger.error(f"JSON parsing error: {je}")
                logger.error(f"Attempted to parse text: {cleaned_text}")
                return None
            
            # Validate question format
            required_keys = ["question", "options", "correct_answer", "explanation", "difficulty"]
            missing_keys = [key for key in required_keys if key not in question_data]
            if missing_keys:
                logger.error(f"Missing required keys: {missing_keys}")
                return None
            
            if len(question_data["options"]) != 4:
                logger.error(f"Invalid number of options: {len(question_data['options'])}")
                return None
            
            if question_data["correct_answer"] not in question_data["options"]:
                logger.error("Correct answer not found in options")
                logger.error(f"Correct answer: {question_data['correct_answer']}")
                logger.error(f"Options: {question_data['options']}")
                return None
            
            return question_data
            
        except Exception as e:
            logger.error(f"Unexpected error in generate_question: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    async def start_game(self, server_id: int, channel_id: int, custom_categories: List[str] = None) -> Dict:
        """Start a new trivia game"""
        if server_id in self.current_games:
            return {"error": "A game is already in progress"}
            
        game_state = {
            "channel_id": channel_id,
            "scores": {},  # user_id -> {points, correct_answers}
            "current_question": None,
            "question_count": 0,
            "max_questions": self.MAX_QUESTIONS,
            "timer": self.DEFAULT_TIMER,
            "active": True,
            "start_time": None,
            "categories": custom_categories or self.categories,
            "last_question_time": None
        }
        
        self.current_games[server_id] = game_state
        return {"success": True, "message": "Game started successfully"}

    async def get_cached_question(self, category: str) -> Optional[Dict]:
        """Get a cached question or generate new ones if cache is empty"""
        if category not in self.question_cache:
            self.question_cache[category] = []
            
        if not self.question_cache[category]:
            # Generate new batch of questions
            questions = []
            for _ in range(self.cache_size):
                question = await self.generate_question(category)
                if question:
                    questions.append(question)
            self.question_cache[category] = questions
            
        if self.question_cache[category]:
            return self.question_cache[category].pop(0)
        return None

    async def next_question(self, server_id: int) -> Optional[Dict]:
        """Get the next question for an active game"""
        if server_id not in self.current_games:
            return {"error": "No active game found"}
        
        game = self.current_games[server_id]
        
        if game["question_count"] >= game["max_questions"]:
            return await self.end_game(server_id)
        
        # Clear the answered users set for the new question
        game["answered_users"] = set()
        
        category = random.choice(game["categories"])
        question = await self.get_cached_question(category)
        if question:
            game["current_question"] = question
            game["question_count"] += 1
            game["last_question_time"] = datetime.now()
            
            return {
                "success": True,
                "question_number": game["question_count"],
                "total_questions": game["max_questions"],
                "category": category,
                **question
            }
        
        return {"error": "Failed to generate question after multiple attempts"}

    async def submit_answer(self, server_id: int, user_id: int, answer: str) -> Dict:
        """Submit and validate an answer"""
        if not self.validate_game_state(server_id):
            return {"error": "No active game or game has timed out"}
        
        game = self.current_games[server_id]
        if not game["active"] or not game["current_question"]:
            return {"error": "No active question"}
        
        # Check if user already answered this question
        if "answered_users" not in game:
            game["answered_users"] = set()
        
        if user_id in game["answered_users"]:
            return {"error": "You already answered this question"}
        
        # Check if time limit exceeded
        time_elapsed = (datetime.now() - game["last_question_time"]).total_seconds()
        if time_elapsed > game["timer"]:
            return {"error": "Time limit exceeded"}
        
        # Mark user as having answered
        game["answered_users"].add(user_id)
        
        correct = answer.lower() == game["current_question"]["correct_answer"].lower()
        
        # Initialize user score if not exists (only tracking correct answers now)
        if user_id not in game["scores"]:
            game["scores"][user_id] = {"correct_answers": 0}
        
        response = {
            "correct": correct,
            "explanation": game["current_question"]["explanation"],
            "correct_answer": game["current_question"]["correct_answer"]
        }
        
        if correct:
            game["scores"][user_id]["correct_answers"] += 1
            
        return response

    async def end_game(self, server_id: int) -> Dict:
        """End the game and return final scores"""
        if server_id not in self.current_games:
            return {"error": "No active game"}
            
        game = self.current_games[server_id]
        game["active"] = False
        
        # Sort players by points and correct answers
        leaderboard = sorted(
            [
                {
                    "user_id": user_id,
                    "points": stats["points"],
                    "correct_answers": stats["correct_answers"]
                }
                for user_id, stats in game["scores"].items()
            ],
            key=lambda x: (x["points"], x["correct_answers"]),
            reverse=True
        )
        
        del self.current_games[server_id]
        
        return {
            "game_over": True,
            "leaderboard": leaderboard,
            "total_questions": game["max_questions"]
        }

    def get_game_state(self, server_id: int) -> Optional[Dict]:
        """Get current game state including scores and progress"""
        game = self.current_games.get(server_id)
        if not game:
            return None
            
        return {
            "active": game["active"],
            "question_count": game["question_count"],
            "max_questions": game["max_questions"],
            "scores": game["scores"],
            "current_question": game["current_question"],
            "time_remaining": (
                game["timer"] - (datetime.now() - game["last_question_time"]).total_seconds()
                if game["last_question_time"]
                else game["timer"]
            )
        }

    async def cancel_game(self, server_id: int) -> Dict:
        """Cancel an ongoing game"""
        if server_id not in self.current_games:
            return {"error": "No active game to cancel"}
            
        del self.current_games[server_id]
        return {"success": True, "message": "Game cancelled successfully"}

    def validate_game_state(self, server_id: int) -> bool:
        """Validate the game state for a server"""
        if server_id not in self.current_games:
            return False
            
        game = self.current_games[server_id]
        if not game["active"]:
            return False
            
        # Check if game has been inactive too long
        if game["last_question_time"]:
            inactive_time = (datetime.now() - game["last_question_time"]).total_seconds()
            if inactive_time > self.DEFAULT_TIMER * 2:  # Game inactive for too long
                logger.info(f"Game {server_id} timed out due to inactivity")
                asyncio.create_task(self.cancel_game(server_id))
                return False
                
        return True

    async def cleanup_stale_games(self):
        """Clean up any stale games"""
        current_time = datetime.now()
        stale_servers = []
        
        for server_id, game in self.current_games.items():
            if game["last_question_time"]:
                inactive_time = (current_time - game["last_question_time"]).total_seconds()
                if inactive_time > self.DEFAULT_TIMER * 2:
                    stale_servers.append(server_id)
                    
        for server_id in stale_servers:
            logger.info(f"Cleaning up stale game for server {server_id}")
            await self.cancel_game(server_id)

class TriviaView(View):
    def __init__(self):
        super().__init__(timeout=30)  # 30 second timeout
        self.value = None

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.green, emoji="▶️", custom_id="continue")
    async def continue_button(self, interaction: discord.Interaction, button: Button):
        self.value = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Stop Game", style=discord.ButtonStyle.red, emoji="🛑", custom_id="stop")
    async def stop_button(self, interaction: discord.Interaction, button: Button):
        self.value = False
        self.stop()
        await interaction.response.defer()

class AnswerView(View):
    def __init__(self, options, trivia_game, server_id):
        super().__init__(timeout=30)
        self.value = None
        self.options = options
        self.trivia_game = trivia_game
        self.server_id = server_id
        self._create_buttons()

    def _create_buttons(self):
        for i, option in enumerate(self.options, 1):
            button = Button(
                label=f"{i}. {option}",
                style=discord.ButtonStyle.blurple,
                custom_id=f"answer_{i}"
            )
            button.callback = self.create_callback(i, option)
            self.add_item(button)

    def create_callback(self, number, option):
        async def callback(interaction: discord.Interaction):
            # Process the answer
            result = await self.trivia_game.submit_answer(
                self.server_id,
                interaction.user.id,
                option
            )

            if "error" in result:
                if result["error"] == "Time limit exceeded":
                    await interaction.response.send_message("⏰ Time's up!", ephemeral=True)
                    return
                if result["error"] == "You already answered this question":
                    await interaction.response.send_message("❌ You've already answered this question!", ephemeral=True)
                    return
                await interaction.response.send_message(f"Error: {result['error']}", ephemeral=True)
                return

            if result["correct"]:
                embed = discord.Embed(
                    title="✅ Correct Answer!",
                    description=f"Great job!"
                )
                embed.add_field(
                    name="Explanation",
                    value=result['explanation'],
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="❌ Incorrect Answer",
                    description="That's not right."
                )
                embed.add_field(
                    name="Correct Answer",
                    value=result['correct_answer'],
                    inline=True
                )
                embed.add_field(
                    name="Explanation",
                    value=result['explanation'],
                    inline=False
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        return callback

class TriviaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.trivia = TriviaGame()
        self.active_messages = {}

    @commands.hybrid_group(name="trivia", invoke_without_command=True)
    async def trivia_group(self, ctx):
        """🎮 Play an exciting trivia game!"""
        embed = discord.Embed(
            title="📚 Trivia Game Commands",
            description=(
                "Test your knowledge with our trivia game!\n\n"
                "**Available Commands**\n"
                "🎮 `/trivia start` - Start a new trivia game\n"
                "📋 `/trivia categories` - Show available categories\n"
                "🛑 `/trivia cancel` - Cancel current game"
            )
        )
        embed.set_footer(text="Have fun playing!")
        await ctx.send(embed=embed)

    @trivia_group.command(name="start")
    @commands.guild_only()
    async def trivia_start(self, ctx):
        """🎮 Start a new trivia game"""
        result = await self.trivia.start_game(ctx.guild.id, ctx.channel.id)
        
        if "error" in result:
            embed = discord.Embed(description=f"❌ {result['error']}")
            await ctx.send(embed=embed)
            return
            
        embed = discord.Embed(
            title="🎮 Trivia Game Starting!",
            description="Get ready for the first question..."
        )
        await ctx.send(embed=embed)
        await self.send_next_question(ctx)

    async def send_next_question(self, ctx):
        """Send the next question with improved UI"""
        question_data = await self.trivia.next_question(ctx.guild.id)
        
        if "error" in question_data:
            embed = discord.Embed(description=f"❌ {question_data['error']}")
            await ctx.send(embed=embed)
            return
            
        if "game_over" in question_data:
            await self.show_final_scores(ctx, question_data)
            return

        category_emoji = self.get_category_emoji(question_data['category'])
        difficulty_emoji = self.get_difficulty_emoji(question_data['difficulty'])
        progress = question_data['question_number'] / question_data['total_questions']
        progress_bar = self.create_progress_bar(progress)

        embed = discord.Embed(
            title=f"Question {question_data['question_number']}/{question_data['total_questions']}",
            description=(
                f"{question_data['question']}\n\n"
                f"{category_emoji} **Category**: {question_data['category']}\n"
                f"{difficulty_emoji} **Difficulty**: {question_data['difficulty'].title()}\n"
                f"⏰ **Time Limit**: {self.trivia.DEFAULT_TIMER} seconds\n\n"
                f"**Progress**\n{progress_bar}"
            )
        )
        
        view = AnswerView(
            options=question_data['options'],
            trivia_game=self.trivia,
            server_id=ctx.guild.id
        )
        message = await ctx.send(embed=embed, view=view)
        
        # Wait for the timer duration
        await asyncio.sleep(self.trivia.DEFAULT_TIMER)
        
        # Disable all buttons after time is up
        for item in view.children:
            item.disabled = True
        
        # Create new embed with the correct answer
        timeout_embed = embed.copy()
        timeout_embed.add_field(
            name="⏰ Time's Up!",
            value=f"**Correct Answer**: {question_data['correct_answer']}\n\n**Explanation**: {question_data['explanation']}",
            inline=False
        )
        
        await message.edit(embed=timeout_embed, view=view)
        
        # Show next question automatically
        continue_msg = await ctx.send("Moving to next question in 5 seconds...")
        await asyncio.sleep(5)
        await continue_msg.delete()
        
        if not view.is_finished():
            view.stop()
        
        # Continue to next question unless game was cancelled
        game_state = self.trivia.get_game_state(ctx.guild.id)
        if game_state and game_state["active"]:
            await self.send_next_question(ctx)

        self.active_messages[ctx.guild.id] = message

    async def show_final_scores(self, ctx, data):
        """Show final scores with improved UI"""
        description = ["🏆 **Final Results**\n"]
        
        for i, player in enumerate(data['leaderboard'], 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, "🏅")
            user = ctx.guild.get_member(player['user_id'])
            name = user.display_name if user else f"User {player['user_id']}"
            
            accuracy = (player['correct_answers']/data['total_questions'])*100
            
            description.append(
                f"\n{medal} **{name}**\n"
                f"└ Correct Answers: **{player['correct_answers']}/{data['total_questions']}**\n"
                f"└ Accuracy: **{accuracy:.1f}%**"
            )
        
        embed = discord.Embed(description="\n".join(description))
        embed.set_footer(text="Thanks for playing! Start a new game with /trivia start")
        await ctx.send(embed=embed)

    def create_progress_bar(self, progress: float) -> str:
        """Create a visual progress bar"""
        bar_length = 10
        filled = int(bar_length * progress)
        empty = bar_length - filled
        return f"`{filled*'■'}{empty*'□'}` {int(progress * 100)}%"

    def get_category_emoji(self, category: str) -> str:
        """Get emoji for category"""
        emoji_map = {
            "General Knowledge": "🎯",
            "Gaming": "🎮",
            "Anime": "🎌",
            "Memes": "😂",
            "Science": "🔬",
            "History": "📜",
            "Geography": "🌍",
            "Movies": "🎬",
            "Technology": "💻",
            "Sports": "⚽",
            "Music": "🎵",
            "Literature": "📚"
        }
        return emoji_map.get(category, "❓")

    def get_difficulty_emoji(self, difficulty: str) -> str:
        """Get emoji for difficulty level"""
        return {
            "easy": "🟢",
            "medium": "🟡",
            "hard": "🔴"
        }.get(difficulty.lower(), "❓")

    @trivia_group.command(name="debug")
    @commands.guild_only()
    async def trivia_debug(self, ctx):
        """Debug command to test API connection"""
        try:
            response = self.trivia.model.generate_content("Say 'hello'")
            await ctx.send(f"API test response: {response.text if response else 'No response'}")
        except Exception as e:
            await ctx.send(f"API test failed: {str(e)}")

    @trivia_group.command(name="stop", aliases=["cancel"])
    @commands.guild_only()
    async def trivia_stop(self, ctx):
        """🛑 Stop the current trivia game"""
        result = await self.trivia.cancel_game(ctx.guild.id)
        
        if "error" in result:
            embed = discord.Embed(description=f"❌ {result['error']}")
            await ctx.send(embed=embed)
            return
            
        embed = discord.Embed(
            title="🛑 Trivia Game Stopped",
            description="The game has been cancelled. Start a new game with `/trivia start`"
        )
        await ctx.send(embed=embed)

    async def cog_load(self):
        """Run when the cog is loaded"""
        self.cleanup_task = self.bot.loop.create_task(self.periodic_cleanup())
        
    async def periodic_cleanup(self):
        """Periodically clean up stale games"""
        while not self.bot.is_closed():
            await self.trivia.cleanup_stale_games()
            await asyncio.sleep(60)  # Check every minute
            
    async def cog_unload(self):
        """Run when the cog is unloaded"""
        if hasattr(self, 'cleanup_task'):
            self.cleanup_task.cancel()

async def setup(bot):
    await bot.add_cog(TriviaCog(bot))
