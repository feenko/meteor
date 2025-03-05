from pathlib import Path

import pytest
import rtoml

from meteor.config import Config
from meteor.config.errors import ConfigDirectoryNotFoundError, ConfigParsingError
from meteor.config.models import Secrets, Settings


@pytest.fixture
def tmp_config_dir(tmp_path: Path):
    config_dir = tmp_path / f'config'
    config_dir.mkdir(parents=True, exist_ok=True)

    return config_dir


class TestConfig:
    @pytest.fixture
    def config(self, tmp_config_dir):
        return Config(directory=tmp_config_dir)

    def test_default_values(self, config):
        assert config.get_secret('bot.token') == Secrets().bot.token
        assert config.get_config('branding.color') == Settings().branding.color
        assert config.get_secret('missing.secret') is None
        assert config.get_config('missing.config') is None

    def test_config_reload(self, config, tmp_config_dir):
        settings_file = tmp_config_dir / 'settings.toml'
        settings = rtoml.load(settings_file) if settings_file.exists() else {}
        settings['branding'] = {'color': '#abcdef'}

        with settings_file.open('w') as f:
            rtoml.dump(settings, f)

        assert config.get_config('branding.color') == Settings().branding.color
        config.reload()
        assert config.get_config('branding.color') == '#abcdef'

    def test_config_overrides(self, config, tmp_config_dir):
        override_path = tmp_config_dir / 'settings.override.toml'
        override_settings = {'branding': {'color': '#123456'}}

        with override_path.open('w') as f:
            rtoml.dump(override_settings, f)

        assert config.get_config('branding.color') == Settings().branding.color
        config.reload()
        assert config.get_config('branding.color') == '#123456'

    def test_missing_config_file(self):
        with pytest.raises(ConfigDirectoryNotFoundError):
            Config(directory='non_existent_directory')

    def test_invalid_config_data(self, tmp_config_dir):
        invalid_settings_file = tmp_config_dir / 'settings.toml'
        with invalid_settings_file.open('w') as f:
            f.write('{"this": "isn\'t", "json": "dummy"}')

        with pytest.raises(ConfigParsingError):
            Config(directory=tmp_config_dir)

    def test_invalid_override_file(self, config, tmp_config_dir):
        override_path = tmp_config_dir / 'settings.override.toml'
        with override_path.open('w') as f:
            f.write('{"this": "isn\'t", "json": "dummy"}')

        with pytest.raises(ConfigParsingError):
            config.reload()
