class ConfigDirectoryNotFoundError(Exception):
    def __init__(self, path: str):
        super().__init__(f"Configuration directory '{path}' not found.")
        self.path = path


class ConfigValidationError(Exception):
    def __init__(self, path: str, message: str):
        super().__init__(f"Configuration validation error in '{path}': {message}")
        self.path = path
        self.message = message


class ConfigParsingError(Exception):
    def __init__(self, path: str, message: str):
        super().__init__(f"Configuration parsing error in '{path}': {message}")
        self.path = path
        self.message = message
