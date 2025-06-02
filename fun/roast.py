import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai
import os
import asyncio
import re

class Roast(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        api_key = os.getenv('GEMINI_API_KEY')
        print(f"API Key length: {len(api_key) if api_key else 'None'}")
        genai.configure(api_key=api_key)
        # Initialize the model once during startup
        self.model = genai.GenerativeModel('gemini-pro')

    @commands.command(name="roast", help="Roasts a user (reply to a message or mention user). Add extra context after command if needed")
    async def roast_command(self, ctx, *args):
        message_content = ""
        member = None
        additional_context = " ".join(args) if args else None

        # Check if the command is used in reply to a message
        if ctx.message.reference:
            try:
                replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                member = replied_msg.author
                message_content = replied_msg.content
                
                # Add additional context if provided
                if additional_context:
                    message_content = f"{message_content} (Additional context: {additional_context})"
            except discord.NotFound:
                await ctx.send("Couldn't find the message you replied to!")
                return
            except Exception as e:
                print(f"Error fetching replied message: {e}")
                await ctx.send("There was an error processing the reply.")
                return
        else:
            # Try to get mentioned user if no reply
            if ctx.message.mentions:
                member = ctx.message.mentions[0]
                message_content = additional_context if additional_context else "their existence"
            else:
                await ctx.send("Please either reply to a message or mention a user to roast!")
                return

        try:
            await self.roast_logic(ctx, member, message_content)
        except Exception as e:
            print(f"Error in roast command: {type(e).__name__} - {str(e)}")
            await ctx.send("Sorry, I encountered an error while generating the roast.")

    @app_commands.command(name="roast", description="Roasts a user")
    @app_commands.describe(
        member="The user to roast",
        context="Additional context for the roast (optional)"
    )
    async def roast_slash(self, interaction: discord.Interaction, member: discord.Member, context: str = None):
        message_content = context if context else "their existence"
        await self.roast_logic(interaction, member, message_content)

    async def roast_logic(self, ctx, member, message_content):
        if not member:
            error_message = "Couldn't identify who to roast!"
            if isinstance(ctx, discord.Interaction):
                await ctx.response.send_message(error_message)
            else:
                await ctx.send(error_message)
            return

        if member.id == self.bot.user.id:
            message = "Nice try, but I'm not roasting myself! 😎"
            if isinstance(ctx, discord.Interaction):
                await ctx.response.send_message(message)
            else:
                await ctx.send(message)
            return

        prompt = f'''You are Aura, a witty Discord bot with a playful personality.
Generate a savage but family-friendly roast for {member.name} based on: "{message_content}"
Rules:
- Must be 1-2 sentences max
- Be creative and witty, but never cruel or inappropriate
- Reference their message/context naturally
- Keep it playful and avoid any offensive content
- No profanity or inappropriate language
- Maximum 30 words
- Make it personal and specific to the context
- Stay within Discord's community guidelines'''

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

        generation_config = {
            "temperature": 1.0,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 100,
        }

        async def generate():
            return await self.bot.loop.run_in_executor(
                None,
                lambda: self.model.generate_content(
                    contents=prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
            )

        for attempt in range(3):
            try:
                response = await asyncio.wait_for(generate(), timeout=10.0)
                
                if not hasattr(response, 'text') or not response.text:
                    raise ValueError("Empty response received")

                roast_response = response.text.strip().strip('"\'')
                roast_response = re.sub(r'@everyone|@here|<@&\d+>', '', roast_response)
                
                if len(roast_response.split()) > 40:
                    raise ValueError("Response too long")

                message = f"{member.mention} {roast_response}"
                if isinstance(ctx, discord.Interaction):
                    await ctx.response.send_message(message)
                else:
                    await ctx.send(message)
                return

            except asyncio.TimeoutError:
                if attempt == 2:
                    raise
                continue
                
            except Exception as e:
                if attempt == 2:
                    raise
                await asyncio.sleep(1)

async def setup(bot):
    await bot.add_cog(Roast(bot))