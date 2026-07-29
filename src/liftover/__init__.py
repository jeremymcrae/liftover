from importlib.metadata import version

__name__ = 'liftover'
__version__ = version(__name__)

from liftover.lifter import get_lifter
from liftover.chain_file import ChainFile, PyTarget

# mimic pyliftover API
LiftOver = get_lifter

__all__ = ['get_lifter', 'ChainFile', 'PyTarget', 'LiftOver']
