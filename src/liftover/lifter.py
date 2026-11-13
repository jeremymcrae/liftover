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


def _has_file(path: str) -> bool:
    return os.path.isfile(path) and os.path.getsize(path) > 0


def get_lifter(target: str | os.PathLike[str],
               query: str | None = None,
               cache: str | os.PathLike[str] | None = None,
               one_based: bool = False,
               chain_server: str = 'https://hgdownload.soe.ucsc.edu',
               cache_dir: str | os.PathLike[str] | None = None) -> ChainFile:
    ''' create a converter to map between genome builds

    Args:
        target: genome build to convert from e.g. 'hg19' or path to chain file
        query: genome build to convert to e.g. 'hg38' or None if target is a chain file
        cache: path to cache folder, defaults to ~/.cache/liftover
        one_based: whether coordinates are one-based (defaults to False)
        chain_server: url to server with chain files, adhering to UCSC's goldenPath URL structure
        cache_dir: alternative parameter for cache folder (matches pyliftover API)

    Returns:
        A ChainFile object capable of converting genome coordinates from the
        target genome to the query genome.
    '''
    if cache is not None and cache_dir is not None:
        raise ValueError("cannot specify both 'cache' and 'cache_dir'")

    if query is None:
        chain_path = os.path.expanduser(os.fspath(target))
        if not chain_path.endswith(('.chain.gz', '.chain')) or os.path.isdir(chain_path):
            raise ValueError('target must be a chain file if no query is provided')
        return ChainFile(chain_path, one_based=one_based)

    if not isinstance(target, str) or not isinstance(query, str):
        raise TypeError('target and query genome builds must be strings')
    target, query = target.strip(), query.strip()
    if not target or not query:
        raise ValueError('target and query genome builds must not be empty')
    if any(sep in b for b in (target, query) for sep in ('/', '\\', '..')):
        raise ValueError(f'invalid genome build name: {target!r}, {query!r}')

    cache = cache if cache is not None else cache_dir
    cache_path = default_cache_dir() if cache is None else os.path.expanduser(os.fspath(cache))

    target = target[0].lower() + target[1:]
    query = query[0].upper() + query[1:]
    basename = f'{target}To{query}.over.chain.gz'
    chain_path = os.path.join(cache_path, basename)

    if cache is None and not _has_file(chain_path):
        legacy_path = os.path.join(os.path.expanduser('~/.liftover'), basename)
        if _has_file(legacy_path):
            return ChainFile(legacy_path, one_based=one_based)

    if not _has_file(chain_path):
        os.makedirs(cache_path, exist_ok=True)
        url = f"{chain_server.rstrip('/')}/goldenPath/{target}/liftOver/{basename}"
        download_file(url, chain_path)

    return ChainFile(chain_path, one_based=one_based)
