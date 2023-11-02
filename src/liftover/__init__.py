from importlib.metadata import version

__name__ = 'liftover'
__version__ = version(__name__)

from liftover.lifter import get_lifter
from liftover.chain_file import ChainFile
