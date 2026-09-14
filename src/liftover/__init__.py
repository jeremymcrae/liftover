from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version('liftover')
except PackageNotFoundError:
    __version__ = 'unknown'

from liftover.lifter import get_lifter, default_cache_dir
from liftover.chain_file import ChainFile, PyTarget

# mimic pyliftover API
LiftOver = get_lifter

__all__ = ['get_lifter', 'ChainFile', 'PyTarget', 'LiftOver', '__version__', 'default_cache_dir']
