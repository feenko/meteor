import logging
from datetime import datetime
from pathlib import Path

from rich.console import Console


class Handler(logging.Handler):
    def __init__(self, formatter=None):
        super().__init__()
        self.console = Console()
        self.formatter = formatter or Formatter()

    def emit(self, record):
        self.console.print(self.formatter.format(record), highlight=False)


class Formatter(logging.Formatter):
    COLORS = {
        'DEBUG': 'slate_blue3',
        'INFO': 'green',
        'WARNING': 'orange1',
        'ERROR': 'bright_red',
        'CRITICAL': 'bright_red',
    }

    def __init__(self):
        super().__init__()
        self.last_time = None

    def format(self, record):
        current_time = self.formatTime(record, '%d %b %H:%M:%S')
        current_time_pretty = (
            f'[grey27]{current_time}[/]' if current_time != self.last_time else ' ' * len(current_time)
        )
        self.last_time = current_time

        name = (record.name[:15] + '..') if len(record.name) > 17 else record.name

        return (
            f'{current_time_pretty} '
            f'[{self.COLORS[record.levelname]}]│ {record.levelname.ljust(8)}[/] '
            f'[{self.COLORS[record.levelname]} dim]{name.rjust(17)}[/] {record.getMessage()}'
        )


def setup_logging():
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)

    for old_log in sorted(logs_dir.glob('*.log'), key=lambda x: x.stat().st_mtime)[:-14]:
        old_log.unlink()

    log_filename = logs_dir / f'{datetime.now():%Y-%m-%d_%H-%M-%S}.log'

    for logger in ('discord', 'asyncio'):
        logging.getLogger(logger).setLevel(logging.ERROR)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(Handler())

    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s'))
    logger.addHandler(file_handler)
