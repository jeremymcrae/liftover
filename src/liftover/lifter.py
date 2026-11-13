
from __future__ import annotations

import os
import sys

from liftover.chain_file import ChainFile
from liftover.download_file import download_file

def default_cache_dir() -> str:
    ''' get the standard user cache directory for liftover (XDG on Unix/macOS) '''
    if sys.platform == 'win32':
        base = os.environ.get('LOCALAPPDATA', '').strip() or os.path.join(os.path.expanduser('~'), 'AppData', 'Local')
    else:
        base = os.environ.get('XDG_CACHE_HOME', '').strip() or os.path.expanduser('~/.cache')
    return os.path.normpath(os.path.join(base, 'liftover'))

def _is_nonempty_file(path: str) -> bool:
    return os.path.isfile(path) and os.path.getsize(path) > 0

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
        cache: path to cache folder, defaults to ~/.cache/liftover
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
        raw_path = os.fspath(target)
        if not isinstance(raw_path, str):
            raise TypeError(f'expected str or os.PathLike[str] for target, got {type(raw_path).__name__}')
        chain_path = os.path.expanduser(raw_path)
        if not chain_path.endswith(('.chain.gz', '.chain')) or os.path.isdir(chain_path):
            raise ValueError('target must be a chain file if no query is provided')
    else:
        # otherwise, construct the chain file path
        if not isinstance(target, str) or not isinstance(query, str):
            raise TypeError('target and query genome builds must be strings')
        target = target.strip()
        query = query.strip()
        if not target or not query:
            raise ValueError('target and query genome builds must not be empty')
        for build in (target, query):
            if '/' in build or '\\' in build or '..' in build:
                raise ValueError(f'invalid genome build name: {build!r}')

        using_default_cache = False
        if cache is None:
            cache = cache_dir

        if cache is None:
            using_default_cache = True
            cache = default_cache_dir()
        else:
            raw_cache = os.fspath(cache)
            if not isinstance(raw_cache, str):
                raise TypeError(f'expected str or os.PathLike[str] for cache, got {type(raw_cache).__name__}')
            cache = os.path.expanduser(raw_cache)

        query = query[0].upper() + query[1:]
        target = target[0].lower() + target[1:]
        basename = f'{target}To{query}.over.chain.gz'
        chain_path = os.path.join(cache, basename)

        # Check legacy ~/.liftover cache as fallback if using default cache location
        if using_default_cache and not _is_nonempty_file(chain_path):
            legacy_path = os.path.join(os.path.expanduser('~/.liftover'), basename)
            if _is_nonempty_file(legacy_path):
                chain_path = legacy_path

        if not _is_nonempty_file(chain_path):
            os.makedirs(cache, exist_ok=True)
            # if the chain file doesn't exist, download it
            server = chain_server.rstrip('/')
            url = f'{server}/goldenPath/{target}/liftOver/{basename}'
            download_file(url, chain_path)

    return ChainFile(chain_path, one_based=one_based)
