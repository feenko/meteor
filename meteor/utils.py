from pathlib import Path


def is_docker() -> bool:
    return Path('/.dockerenv').exists() or Path('/proc/self/cgroup').exists()
