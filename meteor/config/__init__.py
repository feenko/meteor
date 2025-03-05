__all__ = ('CONFIG_FILES', 'Config')

import logging
import os
from pathlib import Path
from typing import Any

import rtoml
from pydantic import BaseModel, ValidationError

from meteor.config.errors import (
    ConfigDirectoryNotFoundError,
    ConfigParsingError,
    ConfigValidationError,
)
from meteor.config.models import Secrets, Settings

_log = logging.getLogger(__name__)

CONFIG_FILES = {
    'secrets': ('secrets.toml', Secrets),
    'settings': ('settings.toml', Settings),
}


class Config:
    def __init__(self, directory: str | Path = 'config') -> None:
        self._cache: dict[str, Any] = {}
        self.directory = Path(directory)
        if not self.directory.exists():
            raise ConfigDirectoryNotFoundError(str(self.directory))
        self._load()

    def _load(self) -> None:
        for config_name, (path, model) in CONFIG_FILES.items():
            full_path = self.directory / Path(path)
            if not full_path.exists():
                self._create_default(full_path, model)

            try:
                config_data = rtoml.load(full_path)
                self._cache_data(config_name, config_data)

                override_path = full_path.with_name(full_path.stem + '.override.toml')
                if override_path.exists():
                    override_data = rtoml.load(override_path)
                    self._cache_data(config_name, override_data, is_override=True)

            except ValidationError as e:
                raise ConfigValidationError(str(full_path), str(e)) from e
            except (rtoml.TomlParsingError, rtoml.TomlSerializationError) as e:
                raise ConfigParsingError(str(full_path), str(e)) from e

    def _create_default(self, path: Path, model: type[BaseModel]) -> None:
        data = model.model_construct().model_dump()
        with path.open('w') as f:
            rtoml.dump(data, f)

    def _merge_configs(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        merged = base.copy()
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged

    def _cache_data(self, name: str, data: dict[str, Any], *, is_override: bool = False) -> None:
        if is_override:
            existing = {k.split('.', 1)[1]: v for k, v in self._cache.items() if k.startswith(f'{name}.')}
            data = self._merge_configs(existing, data) if existing else data
            self._cache = {k: v for k, v in self._cache.items() if not k.startswith(f'{name}.')}

        for key, value in data.items():
            if isinstance(value, dict):
                self._cache_data(f'{name}.{key}', value)
            else:
                self._cache[f'{name}.{key}'] = value

    def _get_env_value(self, name: str, key: str) -> Any | None:
        env_key = f'METEOR_{name.upper()}_{key.replace(".", "_").upper()}'
        return os.environ.get(env_key)

    def _get_cached_value(self, name: str, key: str) -> Any | None:
        return self._get_env_value(name, key) or self._cache.get(f'{name}.{key}')

    def get_secret(self, key: str) -> Any | None:
        return self._get_cached_value('secrets', key)

    def get_config(self, key: str) -> Any | None:
        return self._get_cached_value('settings', key)

    def reload(self) -> None:
        self._load()
