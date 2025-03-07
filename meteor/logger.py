import logging
import traceback
from datetime import datetime
from pathlib import Path

from rich.console import Console


class Handler(logging.Handler):
    def __init__(self, formatter: logging.Formatter | None = None) -> None:
        super().__init__()
        self.console = Console()
        self.formatter = formatter or Formatter()

    def emit(self, record: logging.LogRecord) -> None:
        formatted_message = self.formatter.format(record)
        self.console.print(formatted_message, highlight=False)
        if record.levelno >= logging.ERROR and record.exc_info:
            self.console.print(traceback.format_exc())


class Formatter(logging.Formatter):
    COLORS = {
        'DEBUG': 'slate_blue3',
        'INFO': 'green',
        'WARNING': 'orange1',
        'ERROR': 'bright_red',
        'CRITICAL': 'bright_red',
    }

    def __init__(self) -> None:
        super().__init__()
        self.last_time: str | None = None

    def _format_time(self, current_time: str) -> str:
        if current_time != self.last_time:
            return f'[grey27]{current_time}[/]'
        return ' ' * len(current_time)

    def _update_last_time(self, current_time: str) -> None:
        self.last_time = current_time

    def _format_name(self, name: str, max_length: int = 17) -> str:
        if len(name) > max_length:
            return f'{name[: max_length - 2]}..'
        return name

    def format(self, record: logging.LogRecord) -> str:
        current_time = self.formatTime(record, '%d %b %H:%M:%S')
        formatted_time = self._format_time(current_time)
        self._update_last_time(current_time)

        level_color = self.COLORS.get(record.levelname, 'white')
        logger_name = self._format_name(record.name)
        message = record.getMessage()

        return (
            f'{formatted_time} '
            f'[{level_color}]│ {record.levelname.ljust(8)}[/] '
            f'[{level_color} dim]{logger_name.rjust(17)}[/] {message}'
        )


def setup_logging() -> None:
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)

    _clean_old_logs(logs_dir)

    log_filename = logs_dir / f'{datetime.now():%Y-%m-%d_%H-%M-%S}.log'

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(Handler())

    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s'))
    logger.addHandler(file_handler)

    for logger_name in ('discord', 'asyncio'):
        logging.getLogger(logger_name).setLevel(logging.ERROR)


def _clean_old_logs(logs_dir: Path, keep_count: int = 14) -> None:
    logs = sorted(logs_dir.glob('*.log'), key=lambda p: p.stat().st_mtime)
    for log_file in logs[:-keep_count]:
        log_file.unlink()
