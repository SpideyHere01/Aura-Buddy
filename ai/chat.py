import discord
from discord.ext import commands
import google.generativeai as genai
import asyncio
import logging
import re
from google.auth import exceptions as google_auth_exceptions
from collections import deque
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger('bot.chat')

class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.model = None
        self.setup_model()
        self.conversation_history = {}
        self.max_history = 5
        self.history_expiry = 30

    def setup_model(self):
        try:
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info("Successfully set up Gemini model")
        except google_auth_exceptions.DefaultCredentialsError as e:
            logger.error(f"Failed to set up Gemini model: {e}")

    def remove_mentions(self, content):
        content = content.replace('@everyone', '').replace('@here', '')
        content = re.sub(r'<@&\d+>', '', content)
        return content.strip()

    def contains_link(self, text):
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*$$$$,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        return bool(url_pattern.search(text))

    def get_conversation_history(self, user_id):
        current_time = datetime.now()
        
        if user_id in self.conversation_history:
            history = self.conversation_history[user_id]
            while history and (current_time - history[0]['timestamp']) > timedelta(minutes=self.history_expiry):
                history.popleft()
            
            if not history:
                del self.conversation_history[user_id]
                return []
            
            return history
        return []

    def update_conversation_history(self, user_id, role, content):
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = deque(maxlen=self.max_history)
        
        self.conversation_history[user_id].append({
            'role': role,
            'content': content,
            'timestamp': datetime.now()
        })

    async def generate_response(self, user_id, user_input, referenced_message=None):
        history = self.get_conversation_history(user_id)
        context = "\n".join(f"{msg['role']}: {msg['content']}" for msg in history)
        
        reference_context = f"Referenced message: {referenced_message}\n" if referenced_message else ""
        
        prompt = f'''You are a casual, dank Discord chat bot and also give aura to user.
Your name is Aura and your creator is Urahara Sensei respectively se laadle - do not mention him unless asked.
You have a playful, witty personality with a touch of anime references.
Keep responses extremely short (1-2 sentences max), casual & rizzy (not always only when needed).
Never use profanity, inappropriate language, or send links.
Be a sigma chad bot but maintain respectful boundaries.
Avoid repeating messages or running Discord commands.
Don't use @everyone, @here, or role mentions.
You can mention <@username> if someone asks to tag or mention other user.
If someone seems upset or needs help, be supportive while maintaining your casual style.
{reference_context}Previous messages: {context}
Respond to: {user_input}'''
                
        try:
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    def is_trivia_game_message(self, message: discord.Message) -> bool:
        """Check if the message is part of an active trivia game"""
        # Get the trivia cog
        trivia_cog = self.bot.get_cog('TriviaCog')
        if not trivia_cog:
            return False
            
        # Check if there's an active game in this guild
        game_state = trivia_cog.trivia.get_game_state(message.guild.id if message.guild else None)
        if not game_state or not game_state['active']:
            return False
            
        # Check if the message is in the trivia game channel
        game_channel_id = trivia_cog.trivia.current_games.get(message.guild.id, {}).get("channel_id")
        return message.channel.id == game_channel_id

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        # First check if this is a trivia game message
        if self.is_trivia_game_message(message):
            return  # Ignore chat processing for trivia game messages

        is_mentioned = self.bot.user.mentioned_in(message) and not message.mention_everyone
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_reply = message.reference and message.reference.resolved and message.reference.resolved.author == self.bot.user
        contains_buddy = "buddy" in message.content.lower()

        if is_mentioned or is_dm or is_reply or contains_buddy:
            user_input = re.sub(f'<@!?{self.bot.user.id}>', '', message.content).strip()
            
            if not user_input:
                return

            if not self.model:
                await message.reply("I'm sorry, but I'm having trouble accessing my language model right now. Please try again later.")
                return

            referenced_message = None
            if message.reference and message.reference.resolved:
                referenced_message = message.reference.resolved.content

            async with message.channel.typing():
                for attempt in range(3):
                    try:
                        self.update_conversation_history(message.author.id, "User", user_input)
                        
                        response_text = await self.generate_response(message.author.id, user_input, referenced_message)
                        response_text = self.remove_mentions(response_text.strip())
                        
                        if not response_text:
                            continue
                        
                        self.update_conversation_history(message.author.id, "Assistant", response_text)
                        
                        if self.contains_link(response_text):
                            logger.warning(f"Link detected in response. Original message: {message.content}")
                            await message.reply("I'm sorry, but I can't send links or help you send links.")
                        else:
                            # Check if the response includes a user mention
                            mention_match = re.search(r'@(\w+)', response_text)
                            if mention_match:
                                username = mention_match.group(1)
                                member = discord.utils.get(message.guild.members, name=username)
                                if member:
                                    response_text = response_text.replace(f'@{username}', member.mention)
                            
                            await message.reply(response_text, allowed_mentions=discord.AllowedMentions(users=True))
                        break
                    except Exception as e:
                        logger.error(f"Attempt {attempt + 1}: Error occurred - {str(e)}")
                        if attempt < 2:
                            await asyncio.sleep(2)
                        else:
                            await message.reply("I'm having trouble processing that right now. Please try again later.")
        else:
            logger.debug(f"Ignored message: {message.content}")

async def setup(bot):
    await bot.add_cog(ChatCog(bot))