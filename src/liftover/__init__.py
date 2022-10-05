from pkg_resources import get_distribution

__name__ = 'liftover'
__version__ = get_distribution(__name__).version

from liftover.lifter import get_lifter
from liftover.chain_file import ChainFile
