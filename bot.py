import discord
from discord.ext import commands
from discord import app_commands
import os
import traceback
from dotenv import load_dotenv
import google.generativeai as genai 
import logging
import asyncio
from google.auth import exceptions as google_auth_exceptions
from typing import List
import re

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bot')

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
intents.presences = True  # This covers activities
intents.guilds = True  # Make sure guild intent is enabled
intents.guild_messages = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='.', intents=intents, case_insensitive=True)

    async def setup_hook(self):
        await configure_genai_with_retry()
        await load_all_cogs(self)
        await self.tree.sync()

bot = MyBot()

async def configure_genai_with_retry(max_retries: int = 3, retry_delay: int = 5) -> None:
    for attempt in range(max_retries):
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            logger.info("Successfully configured genai")
            return
        except google_auth_exceptions.DefaultCredentialsError as e:
            logger.warning(f"Failed to configure genai on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
    logger.error("Failed to configure genai after all attempts")

@bot.event
async def on_ready() -> None:
    print(f'Logged in as {bot.user}')
    print('------')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    await setup()

@bot.tree.command(name="commands_list", description="List all registered commands")
async def commands_list(interaction: discord.Interaction) -> None:
    commands = [command.name for command in bot.commands]
    slash_commands = [command.name for command in bot.tree.get_commands()]
    await interaction.response.send_message(f"Registered commands: {', '.join(commands)}\nSlash commands: {', '.join(slash_commands)}")

async def load_extensions(bot: commands.Bot, extensions: List[str]) -> None:
    for extension in extensions:
        try:
            await bot.load_extension(extension)
            logger.info(f"Successfully loaded extension: {extension}")
        except Exception as e:
            logger.error(f"Failed to load extension '{extension}': {e}")
            logger.error(traceback.format_exc())

async def load_all_cogs(bot: commands.Bot) -> None:
    cogs = [
        'cogs.aura', 'cogs.check_aura', 'cogs.daily_aura',
        'cogs.feedback', 'cogs.leaderboard', 'cogs.profile',
        'cogs.randombonus', 'cogs.resetaura', 'cogs.tradeaura', 'cogs.giveaura',
        'cogs.afk', 'cogs.common_cmd', 'cogs.help_command', 'cogs.avatar','cogs.snipe' ,'cogs.bot_join','cogs.enable_disable','cogs.stopwatch','cogs.summary', 'fun.ship',
        'fun.hyper_bakchod_mode', 'fun.lag','fun.roast',
        'fun.tharki', 'fun.flirt', 'fun.lafda','fun.trivia', 'fun.storymode', 'ai.chat', 'shop.add_item','shop.remove_item', 'shop.buy_item',
        'shop.shop_helpers', 'shop.show_shop', 'games.drop', 'games.brainrot_admin', 'games.sell', 'games.inventory', 'games.show_card'
    ]
    await load_extensions(bot, cogs)

@bot.event
async def on_command_error(ctx: commands.Context, error: Exception) -> None:
    if isinstance(error, commands.CommandNotFound):
        if re.match(r'^[a-zA-Z]{2,}$', ctx.invoked_with):
            await ctx.message.add_reaction('❌')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing argument: `{error.param.name}`.")
    else:
        logger.error(f"Error in command '{ctx.command}': {error}")
        await ctx.send("An unexpected error occurred. Please try again later.")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds.", ephemeral=True)
    elif isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("You don't have the required permissions to use this command.", ephemeral=True)
    else:
        logger.error(f"Error in app command: {error}")
        await interaction.response.send_message("An error occurred while processing the command.", ephemeral=True)

@bot.event
async def on_error(event: str, *args, **kwargs) -> None:
    logger.error(f"Error in event {event}: {traceback.format_exc()}")

@bot.event
async def on_shutdown() -> None:
    logger.info("Bot is shutting down...")

@bot.event
async def on_message(message: discord.Message) -> None:
    if bot.user.mentioned_in(message) and "help" in message.content.lower():
        help_command = bot.get_command("help")
        if help_command:
            ctx = await bot.get_context(message)
            await help_command(ctx)
    await bot.process_commands(message)
if __name__ == "__main__":
    if not DISCORD_TOKEN or not GEMINI_API_KEY:
        raise ValueError("DISCORD_TOKEN and GEMINI_API_KEY must be set in .env file")
    try:
        bot.run(DISCORD_TOKEN, reconnect=True)
    except Exception as e:
        logger.error(f"Failed to run the bot: {e}")