import logging
import time

import orjson
from asyncpg import Connection, Pool, create_pool
from discord import CustomActivity
from discord.ext import commands

from meteor.config import Config
from meteor.migrations import Migrations
from meteor.utils import is_docker

_log = logging.getLogger(__name__)


class Client(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.pool: Pool | None = None
        self.boot = time.perf_counter()
        self.config = Config()
        self.owner_ids = frozenset(owner['id'] for owner in self.config.get_config('users.owners'))

    async def _init_pool(self, conn: Connection) -> None:
        await conn.set_type_codec('jsonb', encoder=orjson.dumps, decoder=orjson.loads, schema='pg_catalog')

    async def _create_pool(self) -> None:
        self.pool = await create_pool(
            dsn=self.config.get_secret('database.uri'),
            min_size=3,
            max_size=20,
            init=self._init_pool,
        )

    async def setup_hook(self) -> None:
        await self._create_pool()
        await Migrations(pool=self.pool, config=self.config).execute_schema()
        await self.load_extension('meteor.cogs')

    async def on_message(self, *args, **kwargs) -> None: ...

    async def on_ready(self) -> None:
        _log.info(f'Logged in as {self.user}')
        await self.change_presence(activity=CustomActivity(name=self.config.get_config('bot.status')))
        await self.tree.sync()
        if is_docker():
            _log.info('docker-ok')
        _log.info(f'Synchronized {len(self.tree.get_commands())} command(s)')
        _log.info(f'Boot completed in {time.perf_counter() - self.boot:.2f} seconds')

    async def run(self) -> None:
        await self.start(token=self.config.get_secret('bot.token'), reconnect=True)
