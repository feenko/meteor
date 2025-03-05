from discord import Embed, Interaction, User, app_commands
from discord.ext import commands

from meteor.client import Client


class Info(commands.Cog):
    def __init__(self, bot: Client) -> None:
        self.bot = bot

    info = app_commands.Group(name='info', description='...')

    @info.command(name='user', description='Get detailed information about a user.')
    async def user(self, interaction: Interaction, user: User) -> None:
        embed = Embed(title=f'{user}', description=f'*{user.mention}*')

        await interaction.response.send_message(embed=embed)
