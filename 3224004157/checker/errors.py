"""Expected failures that the command-line interface can explain to the user."""


class CheckerError(Exception):
    """Base class for expected input/output errors."""


class InvalidPathError(CheckerError):
    """A path is relative, invalid, or would overwrite an input file."""


class TextReadError(CheckerError):
    """An input cannot be read as a regular UTF-8 text file."""


class ResultWriteError(CheckerError):
    """The answer cannot be written to the requested destination."""
