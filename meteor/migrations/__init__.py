import logging
from pathlib import Path

import blake3
from asyncpg import Pool

from meteor.config import Config

_log = logging.getLogger(__name__)


class Migrations:
    def __init__(self, *, pool: Pool, config: Config) -> None:
        self.pool = pool
        self.config = config
        self.schema_path = Path(__file__).parent.parent / 'schema.sql'
        self.checksum_path = Path(__file__).parent.parent.parent / '.meteor' / 'SCHEMA_CHECKSUM'

    def _get_stored_hash(self) -> str | None:
        if not self.checksum_path.exists():
            return None
        with self.checksum_path.open() as f:
            return f.read().strip()

    def _store_hash(self, hash_value: str) -> None:
        self.checksum_path.parent.mkdir(parents=True, exist_ok=True)
        with self.checksum_path.open('w') as f:
            f.write(hash_value)

    async def execute_schema(self) -> None:
        try:
            with self.schema_path.open('rb') as f:
                schema_bytes = f.read()
        except FileNotFoundError as e:
            raise FileNotFoundError(f'Schema file not found at {self.schema_path}') from e

        current_hash = blake3.blake3(schema_bytes).hexdigest()
        stored_hash = self._get_stored_hash()

        if stored_hash == current_hash:
            _log.info('Database schema is already up to date')
            return

        _log.info('Database schema requires an update; executing schema update file...')
        try:
            async with self.pool.acquire() as conn:
                schema = schema_bytes.decode('utf-8')
                await conn.execute(schema)
            self._store_hash(current_hash)
            _log.info('Database schema update completed successfully.')
        except Exception as e:
            _log.error(f'Failed to execute database schema: {e}')
            raise
