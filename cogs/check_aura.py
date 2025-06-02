import discord
from discord.ext import commands
from db.mongo import aura_points_collection

class CheckAura(commands.Cog, name="Check Aura"):
    def __init__(self, bot):
        self.bot = bot
        self.LOG_CHANNEL_ID = 1290705365671088211

    @commands.command(name='checkaura', help="Check aura points for yourself or another user")
    async def checkaura_command(self, ctx, member: discord.Member = None):
        await self.checkaura_logic(ctx, member)

    @commands.group(name='check')
    async def check(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @check.command(name='aura')
    async def check_aura(self, ctx, member: discord.Member = None):
        await self.checkaura_logic(ctx, member)

    async def checkaura_logic(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_id = str(member.id)
        user_doc = await aura_points_collection.find_one({"user_id": user_id})
        points = user_doc['points'] if user_doc else 0

        embed = discord.Embed(
            title="🔮 Aura Points Checker",
            color=discord.Color.from_rgb(43, 45, 49)
        )
        
        embed.add_field(
            name="User",
            value=f"{member.mention}",
            inline=True
        )
        
        embed.add_field(
            name="Aura Points",
            value=f"`{points:,}`",
            inline=True
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author.name}")
        
        await self.send_response(ctx, embed=embed)

    async def send_response(self, ctx, content=None, embed=None):
        if isinstance(ctx, discord.Interaction):
            await ctx.response.send_message(content=content, embed=embed)
        else:
            await ctx.send(content=content, embed=embed)

async def setup(bot):
    await bot.add_cog(CheckAura(bot))