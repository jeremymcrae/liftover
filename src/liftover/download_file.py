
from __future__ import annotations

import os
import tempfile

import urllib3

def download_file(url: str, path: str, timeout: float | urllib3.Timeout = 30.0) -> None:
    ''' download a file from a url to a local path

    Args:
        url: the url to download from
        path: the local path to save the file to
        timeout: request timeout in seconds or urllib3.Timeout object (defaults to 30.0)
    '''
    http = urllib3.PoolManager()
    try:
        try:
            r = http.request('GET', url, preload_content=False, timeout=timeout)
        except Exception as e:
            raise ValueError(f'problem accessing {url}: {e}') from e

        try:
            if r.status != 200:
                raise ValueError('problem accessing ' + url)
            
            # create a temporary file in the same directory, and then rename it
            # to the final path. This avoids problems with incomplete downloads.
            dirpath = os.path.dirname(os.path.abspath(path))
            fd, tmp_path = tempfile.mkstemp(dir=dirpath)
            try:
                with os.fdopen(fd, 'wb') as f:
                    for chunk in r.stream(1600):
                        f.write(chunk)
                os.replace(tmp_path, path)
            except BaseException:
                os.unlink(tmp_path)
                raise
        finally:
            r.release_conn()
    finally:
        http.clear()
