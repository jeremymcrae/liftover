
import os

from liftover.chain_file import ChainFile
from liftover.download_file import download_file

import requests

def get_lifter(target, query, cache=None):
    ''' create a converter to map between genome builds
    
    Args:
        target: genome build to convert from e.g. 'hg19'
        source: genome build to convert to e.g. 'hg38'
        cache: path to cache folder, defaults to ~/.liftover
    
    Returns:
        A ChainFile object capable of converting genome coordinates from the
        target genome to the query genome.
    '''
    
    if cache is None:
        cache = os.path.expanduser('~/.liftover')
    
    if not os.path.exists(cache):
        os.mkdir(cache)
    
    query = query[0].upper() + query[1:]
    target = target[0].lower() + target[1:]
    basename = '{}To{}.over.chain.gz'.format(target, query)
    chain_path = os.path.join(cache, basename)
    
    if not os.path.exists(chain_path):
        url = 'http://hgdownload.cse.ucsc.edu/goldenPath/{}/liftOver/{}'.format(target, basename)
        download_file(url, chain_path)
    
    return ChainFile(chain_path, target, query)
