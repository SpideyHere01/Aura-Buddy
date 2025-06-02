import discord
from discord.ext import commands
import google.generativeai as genai
import os
from typing import Optional
import asyncio

class SummaryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        api_key = os.getenv('GOOGLE_API_KEY')  
        self.genai = genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        
    async def get_messages_to_summarize(self, ctx: commands.Context, message: Optional[discord.Message] = None) -> list[str]:
        """Get messages to summarize, either from a reply or the last 50 messages"""
        messages = []
        
        if message:  
            async for msg in ctx.channel.history(limit=50, before=message):
                if not msg.content.strip():  
                    continue
                messages.append(f"{msg.author.name}: {msg.content}")
            messages.reverse()
            messages.append(f"{message.author.name}: {message.content}")
        else:  
            async for msg in ctx.channel.history(limit=50):
                if not msg.content.strip():
                    continue
                messages.append(f"{msg.author.name}: {msg.content}")
            messages.reverse()
            
        return messages

    async def get_summary_from_gemini(self, messages: list[str], attempt: int = 1) -> str:
        """Get summary from Gemini with robust error handling"""
        try:
            prompt = f"""Please provide a clear and concise summary of the following chat conversation. 
            Focus on the main topics and key points discussed, while maintaining a neutral tone.
            Avoid repeating usernames or using direct quotes.
            If there's any inappropriate content or sensitive content, handle it gracefully, try including it without use of inappropriate language.

            Chat History:
            {'\n'.join(messages)}

            Summary:"""

            generation_config = {
                'temperature': 0.5,
                'max_output_tokens': 2048
            }
            response = await asyncio.to_thread(
                lambda: self.model.generate_content(
                    prompt, 
                    generation_config=generation_config,
                )
            )

            if not response.candidates:
                if hasattr(response, 'prompt_feedback'):
                    print(f"Prompt Feedback: {response.prompt_feedback}")
                return "Unable to generate summary."

            summary = response.text if hasattr(response, 'text') else "Unable to generate summary."
            return summary

        except Exception as e:
            print(f"Failed with error: {str(e)}")
            return "I apologize, but I'm unable to provide a summary at this time."

    @commands.command(name="summarize")
    async def summarize(self, ctx: commands.Context):
        """Summarize the last 50 messages or messages above a replied message"""
        async with ctx.typing():
            try:
                reference = ctx.message.reference
                reference_message = None
                if reference and reference.message_id:
                    reference_message = await ctx.channel.fetch_message(reference.message_id)

                messages = await self.get_messages_to_summarize(ctx, reference_message)
                
                if not messages:
                    await ctx.reply("No messages found to summarize!")
                    return

                summary = await self.get_summary_from_gemini(messages)

                embed = discord.Embed(
                    title="Chat Summary",
                    description=summary,
                    color=discord.Color.blue()
                )
                embed.set_footer(text=f"Summarized {len(messages)} messages")
                
                await ctx.reply(embed=embed)

            except Exception as e:
                error_embed = discord.Embed(
                    title="Error",
                    description="An error occurred while generating the summary. Please try again later.",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=error_embed)
                print(f"Error in summarize command: {str(e)}")

async def setup(bot):
    await bot.add_cog(SummaryCog(bot))
