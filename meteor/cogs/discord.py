from discord import ButtonStyle, Embed, Interaction, User, app_commands
from discord.ext import commands
from discord.ui import Button, View

from meteor.client import Client


class DiscordUserView(View):
    def __init__(self, user: User):
        super().__init__()
        self.add_item(Button(label='Avatar URL', url=user.display_avatar.url, style=ButtonStyle.link))
        self.add_item(
            Button(
                label='Banner URL',
                url=user.banner.url if user.banner else 'https://meteors.cc',
                disabled=not user.banner,
                style=ButtonStyle.link,
            )
        )


class Discord(commands.Cog):
    def __init__(self, bot: Client) -> None:
        self.bot = bot

    discord = app_commands.Group(name='discord', description='...')

    @discord.command(name='user', description='Get detailed information about a user.')
    async def user(self, interaction: Interaction, user: User) -> None:
        user = await self.bot.fetch_user(user.id)
        member = interaction.guild.get_member(user.id)

        join_position = (
            (
                sum(
                    m.joined_at < member.joined_at
                    for m in interaction.guild.members
                    if m.joined_at is not None
                )
                + 1
            )
            if member
            else None
        )

        embed = (
            Embed(
                color=int(
                    self.bot.config.get_config('bot.color'), 16
                ),  # TODO: automatically grab color from config
            )
            .set_author(
                name=(f'{user.global_name} (@{user.name})' if user.global_name else f'{user.name}'),
                icon_url=user.display_avatar.url,
                url=f'https://discord.com/users/{user.id}',
            )
            .set_thumbnail(url=user.display_avatar.url)
            .set_image(url=user.banner.url if user.banner else None)
            .add_field(
                name='Generic',
                value=(
                    f'ID: {user.id}\n'
                    + (
                        f'Join position: {join_position}/{len(interaction.guild.members)}\n'
                        if join_position
                        else ''
                    )
                    + f'Mutual guilds: {len(user.mutual_guilds)}\n'
                ),
                inline=False,
            )
            .add_field(
                name='Dates',
                value=(
                    f'Created at: <t:{int(user.created_at.timestamp())}:R>\n'
                    + (f'Joined at: <t:{int(member.joined_at.timestamp())}:R>\n' if member else '')
                    + (
                        f'Booster since: <t:{int(member.premium_since.timestamp())}:R>\n'
                        if member and member.premium_since
                        else ''
                    )
                ),
                inline=False,
            )
        )

        await interaction.response.send_message(embed=embed, view=DiscordUserView(user))
