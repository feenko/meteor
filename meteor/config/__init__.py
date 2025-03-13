__all__ = ('CONFIG_FILES', 'Config')

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

CONFIG_FILES = {
    'secrets': ('secrets.toml', Secrets),
    'settings': ('settings.toml', Settings),
}


class Config:
    def __init__(self, directory: str | Path = 'config') -> None:
        self._cache: dict[str, Any] = {}
        self.directory = Path(directory)
        if not self.directory.exists():
            raise ConfigDirectoryNotFoundError(f'Config directory not found: {self.directory}')
        self._load()

    def _load(self) -> None:
        for config_name, (path, model) in CONFIG_FILES.items():
            full_path = self.directory / Path(path)
            if not full_path.exists():
                self._create_default(full_path, model)

            try:
                base_data = rtoml.load(full_path)
                validated_base = model(**base_data)
                base_dict = validated_base.model_dump()

                override_path = full_path.with_name(f'{full_path.stem}.override.toml')
                if override_path.exists():
                    override_data = rtoml.load(override_path)
                    merged_dict = self._merge_configs(base_dict, override_data)
                    try:
                        validated_merged = model(**merged_dict)
                        merged_dict = validated_merged.model_dump()
                    except ValidationError as e:
                        raise ConfigValidationError(
                            f'Validation error in merged configuration from {override_path}: {e}'
                        ) from e
                else:
                    merged_dict = base_dict

                self._cache_data(config_name, merged_dict)

            except ValidationError as e:
                raise ConfigValidationError(f'Validation error in {full_path}: {e}') from e
            except (rtoml.TomlParsingError, rtoml.TomlSerializationError) as e:
                raise ConfigParsingError(f'Parsing error in {full_path}: {e}') from e

    def _create_default(self, path: Path, model: type[BaseModel]) -> None:
        default_data = model.model_construct().model_dump()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w') as f:
            rtoml.dump(default_data, f)

    def _merge_configs(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        merged = base.copy()
        for key, override_value in override.items():
            base_value = merged.get(key)
            if isinstance(base_value, dict) and isinstance(override_value, dict):
                merged[key] = self._merge_configs(base_value, override_value)
            elif isinstance(base_value, dict) and not isinstance(override_value, dict):
                raise ValueError(f"Cannot merge non-dict value for key '{key}' into existing dict")
            else:
                merged[key] = override_value
        return merged

    def _cache_data(self, name: str, data: dict[str, Any]) -> None:
        for key, value in data.items():
            if isinstance(value, dict):
                self._cache_data(f'{name}.{key}', value)
            else:
                self._cache[f'{name}.{key}'] = value

    def _get_env_value(self, config_name: str, key: str) -> Any | None:
        env_key = f'METEOR_{config_name.upper()}_{key.replace(".", "_").upper()}'
        return os.environ.get(env_key)

    def _get_cached_value(self, config_name: str, key: str) -> Any | None:
        return self._get_env_value(config_name, key) or self._cache.get(f'{config_name}.{key}')

    def get_secret(self, key: str) -> Any | None:
        return self._get_cached_value('secrets', key)

    def get_config(self, key: str) -> Any | None:
        return self._get_cached_value('settings', key)

    def reload(self) -> None:
        self._cache.clear()
        self._load()
