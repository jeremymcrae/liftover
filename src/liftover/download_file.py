
import os
import tempfile

import urllib3

def download_file(url: str, path: str) -> None:
    ''' download a file from a url to a local path

    Args:
        url: the url to download from
        path: the local path to save the file to
    '''
    http = urllib3.PoolManager()
    r = http.request('GET', url, preload_content=False)
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
            os.rename(tmp_path, path)
        except BaseException:
            os.unlink(tmp_path)
            raise
    finally:
        # ensure we release the connection and clear the pool
        r.release_conn()
        http.clear()
