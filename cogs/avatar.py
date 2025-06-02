import discord
from discord.ext import commands
from discord import app_commands

class Avatar(commands.Cog, name="Avatar"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='av', aliases=['avatar'], help="Displays the avatar/banner of the user or a mentioned user.")
    async def avatar_command(self, ctx: commands.Context, member: discord.Member = None):
        await self.avatar_logic(ctx, member)

    @app_commands.command(name='avatar', description="Displays the avatar/banner of the user or a mentioned user.")
    async def avatar_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        await self.avatar_logic(interaction, member)

    async def avatar_logic(self, ctx, member: discord.Member = None):
        try:
            member = member or (ctx.author if isinstance(ctx, commands.Context) else ctx.user)
            requester = ctx.author if isinstance(ctx, commands.Context) else ctx.user

            class DownloadModal(discord.ui.Modal, title="Download Avatar"):
                def __init__(self, url):
                    super().__init__()
                    self.url = url

                async def on_submit(self, interaction: discord.Interaction):
                    await interaction.response.send_message(
                        f"Right click and 'Save As' to download:\n{self.url}",
                        ephemeral=True
                    )

            class AvatarView(discord.ui.View):
                def __init__(self, cog, member, requester):
                    super().__init__(timeout=60)
                    self.cog = cog
                    self.member = member
                    self.requester = requester
                    self.current_view = "avatar"  # Track current view

                @discord.ui.button(label="Avatar", style=discord.ButtonStyle.primary)
                async def avatar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    embed = await self.cog.create_avatar_embed(self.member, self.requester)
                    self.current_view = "avatar"  # Update current view
                    await interaction.response.edit_message(embed=embed, view=self)

                @discord.ui.button(label="Banner", style=discord.ButtonStyle.secondary)
                async def banner_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    embed = await self.cog.create_banner_embed(self.member, self.requester)
                    self.current_view = "banner"  # Update current view
                    await interaction.response.edit_message(embed=embed, view=self)
                
                @discord.ui.button(label="Download", style=discord.ButtonStyle.green)
                async def download_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if self.current_view == "avatar":
                        url = self.member.display_avatar.with_size(4096).url
                    else:  # banner
                        user = await self.cog.bot.fetch_user(self.member.id)
                        url = user.banner.url if user.banner else None
                        if not url:
                            await interaction.response.send_message(
                                "This user doesn't have a banner to download!",
                                ephemeral=True
                            )
                            return

                    await interaction.response.send_message(
                        f"Right click and 'Save As' to download:\n{url}",
                        ephemeral=True
                    )

            view = AvatarView(self, member, requester)
            initial_embed = await self.create_avatar_embed(member, requester)
            await self.send_response(ctx, embed=initial_embed, view=view)

        except Exception as e:
            print(f"Avatar/Banner Error: {e}")
            await self.send_response(ctx, "An error occurred while fetching the avatar/banner.")

    async def create_avatar_embed(self, member: discord.Member, requester: discord.Member):
        avatar_url = member.display_avatar.url
        embed = discord.Embed(
            description=f"Here is {member.mention}'s avatar.",
            color=discord.Color.from_rgb(43, 45, 49)
        )
        embed.set_author(name=f"{member.display_name}'s Avatar", icon_url=avatar_url)
        embed.set_image(url=avatar_url)
        embed.set_footer(text=f"Requested by {requester.display_name}", icon_url=requester.display_avatar.url)
        return embed

    async def create_banner_embed(self, member: discord.Member, requester: discord.Member):
        try:
            user = await self.bot.fetch_user(member.id)
            banner_url = user.banner.url if user.banner else None

            embed = discord.Embed(
                description=f"Here is {member.mention}'s banner." if banner_url else f"{member.mention} has no banner set.",
                color=discord.Color.from_rgb(43, 45, 49)
            )
            embed.set_author(name=f"{member.display_name}'s Banner", icon_url=member.display_avatar.url)
            if banner_url:
                embed.set_image(url=banner_url)
            embed.set_footer(text=f"Requested by {requester.display_name}", icon_url=requester.display_avatar.url)
            return embed
        except Exception as e:
            print(f"Banner Error: {e}")
            embed = discord.Embed(
                description=f"Unable to fetch banner for {member.mention}.",
                color=discord.Color.from_rgb(43, 45, 49)
            )
            embed.set_author(name=f"{member.display_name}'s Banner", icon_url=member.display_avatar.url)
            embed.set_footer(text=f"Requested by {requester.display_name}", icon_url=requester.display_avatar.url)
            return embed

    async def send_response(self, ctx, content=None, embed=None, view=None):
        if isinstance(ctx, discord.Interaction):
            return await ctx.response.send_message(content=content, embed=embed, view=view)
        else:
            return await ctx.send(content=content, embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(Avatar(bot)) 