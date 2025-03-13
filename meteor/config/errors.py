class ConfigDirectoryNotFoundError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class ConfigValidationError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class ConfigParsingError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

