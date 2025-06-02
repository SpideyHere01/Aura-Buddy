import discord
from discord import app_commands
import os
import asyncio
import random
from discord.ext import commands
import google.generativeai as genai
import re

class Lag(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

    @commands.command(name='lag', help='Pretend to type with lag')
    async def lag_command(self, ctx):
        await self.lag_logic(ctx)

    @app_commands.command(name='lag', description='Pretend to type with lag')
    async def lag_slash(self, interaction: discord.Interaction):
        await self.lag_logic(interaction)

    async def lag_logic(self, ctx):
        thinking_messages = [
            "Hold on, I'm thinking... 🤔", 
            "Just a sec... deep thoughts loading... 💭", 
            "Calculating the meaning of life... 🌌",
            "Uh oh, my brain is lagging... 🐌",
            "Be right back... I think I dropped my thoughts somewhere... 🔍",
            "Loading response.exe... progress: 13%... 🔄",
            "Did someone unplug my brain? 🔌",
            "Error 404: Quick response not found 😅"
        ]
        
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

        if isinstance(ctx, discord.Interaction):
            await ctx.response.send_message(random.choice(thinking_messages))
            message = await ctx.original_response()
        else:
            message = await ctx.send(random.choice(thinking_messages))
        
        try:
            for _ in range(random.randint(2, 4)):
                await asyncio.sleep(random.randint(3, 7))
                await message.edit(content=random.choice(thinking_messages))

            prompt = '''You are Aura, a playful Discord bot.
Generate a funny excuse for why you were lagging.
Rules:
- Include at least one emoji
- Reference gaming, internet, or tech humor
- Be creative and unexpected
- Keep it short and punchy (max 20 words)
- Add personality with internet slang or meme references
- Make it relatable to Discord users'''

            response = await asyncio.wait_for(
                self.bot.loop.run_in_executor(
                    None,
                    lambda: genai.GenerativeModel('gemini-pro').generate_content(
                        prompt,
                        safety_settings=safety_settings
                    )
                ),
                timeout=10.0
            )
            
            final_response = response.text.strip()
            final_response = re.sub(r'@everyone|@here|<@&\d+>', '', final_response)
            
            await message.edit(content=final_response)
            
        except Exception as e:
            await message.edit(content="Oops, my brain.exe stopped working! 🤖💫")
            print(f"Error in lag command: {e}")

async def setup(bot):
    await bot.add_cog(Lag(bot))
