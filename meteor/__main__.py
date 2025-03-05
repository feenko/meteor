import asyncio
import logging

from discord import AllowedMentions, Intents

from meteor.client import Client
from meteor.logger import setup_logging

try:
    import uvloop  # type: ignore
except ModuleNotFoundError:
    _HAS_UVLOOP = False
else:
    _HAS_UVLOOP = True

setup_logging()

_log = logging.getLogger('meteor')


async def runner():
    client = Client(
        intents=Intents.all(),
        command_prefix=None,
        help_command=None,
        allowed_mentions=AllowedMentions(
            everyone=False,
            users=False,
            roles=False,
            replied_user=False,
        ),
    )

    async with client:
        await client.run()


if __name__ == '__main__':
    try:
        if _HAS_UVLOOP:
            _log.info('Using uvloop event loop.')
            uvloop.run(runner())
        else:
            _log.warning('Using asyncio event loop. For production environments, use uvloop.')
            asyncio.run(runner())
    except KeyboardInterrupt:
        _log.critical('Process interrupted by user.')
