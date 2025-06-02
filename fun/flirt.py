import discord
from discord import app_commands
import os
import google.generativeai as genai
from discord.ext import commands
import re

class Flirt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

    @commands.command(name='flirt', help="Send a flirty compliment")
    async def flirt_command(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author
        await self.flirt_logic(ctx, user)

    @app_commands.command(name='flirt', description="Send a flirty compliment")
    async def flirt_slash(self, interaction: discord.Interaction, user: discord.Member = None):
        if user is None:
            user = interaction.user
        await self.flirt_logic(interaction, user)

    async def flirt_logic(self, ctx, user):
        prompt = f'''You are Aura, a witty Discord bot with a playful personality.
Generate a short, wholesome compliment for {user.name}.
Rules:
- Keep it casual and fun, like a friendly Discord message
- Include one emoji for personality
- Focus on positive vibes or achievements
- Maximum 20 words
- Make it sound natural, not formal
- Add a touch of humor when appropriate
- Never be inappropriate or too personal'''

        try:
            model = genai.GenerativeModel('gemini-pro')
            
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
            
            response = model.generate_content(
                prompt,
                safety_settings=safety_settings
            )
            
            compliment = response.text.strip()
            compliment = re.sub(r'@everyone|@here|<@&\d+>', '', compliment)
            
            message = f"{user.mention}, {compliment}"
            if isinstance(ctx, discord.Interaction):
                await ctx.response.send_message(message)
            else:
                await ctx.send(message)
        except Exception as e:
            error_message = f"An error occurred while processing your command: {str(e)}"
            if isinstance(ctx, discord.Interaction):
                if ctx.response.is_done():
                    await ctx.followup.send(error_message)
                else:
                    await ctx.response.send_message(error_message)
            else:
                await ctx.send(error_message)
            print(f"Error in flirt command: {e}")

async def setup(bot):
    await bot.add_cog(Flirt(bot))