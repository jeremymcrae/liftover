
from __future__ import annotations

import os

from liftover.chain_file import ChainFile
from liftover.download_file import download_file

def get_lifter(target: str | os.PathLike[str],
               query: str | None=None,
               cache: str | os.PathLike[str] | None=None,
               one_based: bool=False,
               chain_server: str='https://hgdownload.soe.ucsc.edu',
               cache_dir: str | os.PathLike[str] | None=None) -> ChainFile:
    ''' create a converter to map between genome builds

    Args:
        target: genome build to convert from e.g. 'hg19' or path to chain file
        query: genome build to convert to e.g. 'hg38' or None if target is a chain file
        cache: path to cache folder, defaults to ~/.liftover
        one_based: whether coordinates are one-based (defaults to False)
        chain_server: url to server with chain files. This allows for mirrors of
            the UCSC chain files, but they need to adhere to the UCSC url structure
            e.g. https://hgdownload.soe.ucsc.edu/goldenPath/hg38/liftOver/hg38ToHg19.over.chain.gz
            or https://www.example.org/folder/goldenPath/hg38/liftOver/hg38ToHg19.over.chain.gz
        cache_dir: alternative parameter for cache folder (matches pyliftover API)

    Returns:
        A ChainFile object capable of converting genome coordinates from the
        target genome to the query genome.
    '''

    # handle cache_dir parameter (matches pyliftover interface)
    if cache is not None and cache_dir is not None:
        raise ValueError("cannot specify both 'cache' and 'cache_dir'")

    if query is None:
        # if no query is provided, assume the target is a chain file
        chain_path = os.fspath(target)
        if not chain_path.endswith(('.chain.gz', '.chain')) or os.path.isdir(chain_path):
            raise ValueError('target must be a chain file if no query is provided')
    else:
        # otherwise, construct the chain file path
        target = str(target).strip()
        query = query.strip()
        if not target or not query:
            raise ValueError('target and query genome builds must not be empty')

        if cache is None:
            cache = cache_dir

        if cache is None:
            cache = os.path.expanduser('~/.liftover')
        else:
            cache = os.path.expanduser(os.fspath(cache))

        query = query[0].upper() + query[1:]
        target = target[0].lower() + target[1:]
        basename = '{}To{}.over.chain.gz'.format(target, query)
        chain_path = os.path.join(cache, basename)
        
        if not os.path.exists(chain_path):
            os.makedirs(cache, exist_ok=True)
            # if the chain file doesn't exist, download it
            server = chain_server.rstrip('/')
            url = f'{server}/goldenPath/{target}/liftOver/{basename}'
            download_file(url, chain_path)

    return ChainFile(chain_path, one_based=one_based)
