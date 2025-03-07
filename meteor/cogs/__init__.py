import logging

from meteor.cogs.discord import Discord

_log = logging.getLogger(__name__)


async def setup(bot) -> None:
    modules = (Discord(bot),)
    for module in modules:
        await bot.add_cog(module)
    cog_names = ', '.join(module.__class__.__name__ for module in modules)
    _log.info(f'Loaded the following cogs: {cog_names}')
