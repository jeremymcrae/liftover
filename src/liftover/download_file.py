from __future__ import annotations

import gzip
import os
import uuid

import urllib3


def _verify_gzip(path: str, url: str) -> None:
    try:
        with gzip.open(path, 'rb') as gz:
            while gz.read(1024 * 1024):
                pass
    except Exception as e:
        raise ValueError(f'downloaded file from {url} is not a valid gzip file: {e}') from e


def download_file(url: str, path: str, timeout: float | urllib3.Timeout = 30.0) -> None:
    ''' download a file from a url to a local path '''
    is_gzip = path.endswith('.gz')
    tmp_path = f'{path}.{uuid.uuid4().hex}.tmp'
    http = urllib3.PoolManager()
    try:
        r = http.request('GET', url, preload_content=False, timeout=timeout)
        try:
            if r.status != 200:
                raise ValueError(f'problem accessing {url}: HTTP {r.status}')

            total_bytes = 0
            with open(tmp_path, 'xb') as f:
                for chunk in r.stream(65536, decode_content=not is_gzip):
                    f.write(chunk)
                    total_bytes += len(chunk)
        finally:
            r.release_conn()

        if total_bytes == 0:
            raise ValueError(f'problem downloading from {url}: received empty response')

        headers = getattr(r, 'headers', None)
        encoding = headers.get('Content-Encoding') if headers else None
        content_length = headers.get('Content-Length') if headers else None
        if (
            (is_gzip or not encoding or encoding.strip().lower() == 'identity')
            and isinstance(content_length, str)
            and content_length.strip().isdigit()
        ):
            expected = int(content_length)
            if total_bytes != expected:
                raise ValueError(
                    f'incomplete download from {url}: received {total_bytes} bytes, expected {expected}'
                )

        if is_gzip:
            _verify_gzip(tmp_path, url)

        os.replace(tmp_path, path)
    except BaseException as e:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        if isinstance(e, urllib3.exceptions.HTTPError):
            raise ValueError(f'problem accessing {url}: {e}') from e
        raise
    finally:
        http.clear()
