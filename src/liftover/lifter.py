
import os

from liftover.chain_file import ChainFile
from liftover.download_file import download_file

def get_lifter(target: str,
               query: str=None,
               cache: str=None,
               one_based: bool=False,
               chain_server: str='https://hgdownload.soe.ucsc.edu',
               **kwargs):
    ''' create a converter to map between genome builds

    Args:
        target: genome build to convert from e.g. 'hg19' or path to chain file
        query: genome build to convert to e.g. 'hg38' or None if target is a chain file
        cache: path to cache folder, defaults to ~/.liftover
        chain_server: url to server with chain files. This allows for mirrors of
            the UCSC chain files, but they need to adhere to the UCSC url structure
            e.g. https://hgdownload.soe.ucsc.edu/goldenPath/hg38/liftOver/hg38ToHg19.over.chain.gz
            or https://www.example.org/folder/goldenPath/hg38/liftOver/hg38ToHg19.over.chain.gz

    Returns:
        A ChainFile object capable of converting genome coordinates from the
        target genome to the query genome.
    '''

    # check for cache directory in kwargs (matches pyliftover interface)
    if 'cache_dir' in kwargs:
        cache = kwargs['cache_dir']

    if cache is None:
        cache = os.path.expanduser('~/.liftover')

    os.makedirs(cache, exist_ok=True)

    if query is None:
        # if no query is provided, assume the target is a chain file
        if target.endswith('.chain.gz'):    
            chain_path = target
        else:
            raise ValueError('target must be a chain file if no query is provided')
    else:
        # otherwise, construct the chain file path
        query = query[0].upper() + query[1:]
        target = target[0].lower() + target[1:]
        basename = '{}To{}.over.chain.gz'.format(target, query)
        chain_path = os.path.join(cache, basename)
        
        if not os.path.exists(chain_path):
            # if the chain file doesn't exist, download it
            url = f'{chain_server}/goldenpath/{target}/liftOver/{basename}'
            download_file(url, chain_path)

    return ChainFile(chain_path, one_based=one_based)
