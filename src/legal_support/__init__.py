"""Legal Support.

Example:
    >>> from legal_support import __version__
    >>> print(__version__)
    0.1.0

License:
    Code: Apache License 2.0
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("legal_support")
except PackageNotFoundError:
    __version__ = "0.1.0"

__all__ = ["__version__"]
