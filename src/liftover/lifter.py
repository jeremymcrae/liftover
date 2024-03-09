
import os

from liftover.chain_file import ChainFile
from liftover.download_file import download_file

def get_lifter(target: str, query: str, cache: str=None, one_based=False, chain_server='https://hgdownload.soe.ucsc.edu'):
    ''' create a converter to map between genome builds

    Args:
        target: genome build to convert from e.g. 'hg19'
        source: genome build to convert to e.g. 'hg38'
        cache: path to cache folder, defaults to ~/.liftover
        chain_server: url to server with chain files. This allows for mirrors of
            the UCSC chain files, but they need to adhere to the UCSC url structure
            e.g. https://hgdownload.soe.ucsc.edu/goldenPath/hg38/liftOver/hg38ToHg19.over.chain.gz
            or https://www.example.org/folder/goldenPath/hg38/liftOver/hg38ToHg19.over.chain.gz

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
        url = f'{chain_server}/goldenpath/{target}/liftOver/{basename}'
        download_file(url, chain_path)

    return ChainFile(chain_path, one_based=one_based)
