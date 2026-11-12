from __future__ import annotations

import gzip
import os
import uuid
from typing import TYPE_CHECKING, Any

import urllib3

if TYPE_CHECKING:
    from urllib3.response import BaseHTTPResponse


def verify_file(
    path: str,
    url: str,
    total_bytes: int,
    content_length: Any = None,
    is_gzip: bool = False,
) -> None:
    ''' verify downloaded file is non-empty, matches Content-Length, and has valid gzip format '''
    if total_bytes == 0:
        raise ValueError(f'problem downloading from {url}: received empty response')

    if isinstance(content_length, str) and content_length.strip().isdigit():
        expected = int(content_length.strip())
        if total_bytes != expected:
            raise ValueError(
                f'incomplete download from {url}: received {total_bytes} bytes, expected {expected}'
            )

    if is_gzip:
        try:
            with gzip.open(path, 'rb') as gz:
                while gz.read(1024 * 1024):
                    pass
        except Exception as e:
            raise ValueError(f'downloaded file from {url} is not a valid gzip file: {e}') from e

def _create_temp_path(dirpath: str) -> tuple[int, str]:
    ''' create an exclusive temporary file respecting the process umask '''
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_BINARY', 0)
    for _ in range(16):
        tmp_path = os.path.join(dirpath, f'.liftover-{uuid.uuid4().hex}.tmp')
        try:
            fd = os.open(tmp_path, flags, 0o666)
            return fd, tmp_path
        except FileExistsError:
            continue
    raise FileExistsError(f'could not create temporary download file in {dirpath}')

def _stream_to_file(response: BaseHTTPResponse, dest_path: str, url: str) -> None:
    ''' stream response body to a temporary file, verify integrity, and atomically rename '''
    dirpath = os.path.dirname(os.path.abspath(dest_path))
    is_gzip = dest_path.endswith(('.gz', '.chain.gz'))
    fd, tmp_path = _create_temp_path(dirpath)
    f = None
    try:
        f = os.fdopen(fd, 'wb')
    except BaseException:
        os.close(fd)
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    try:
        total_bytes = 0
        try:
            with f:
                for chunk in response.stream(65536, decode_content=not is_gzip):
                    f.write(chunk)
                    total_bytes += len(chunk)
        except urllib3.exceptions.HTTPError as e:
            raise ValueError(f'problem downloading from {url}: {e}') from e

        headers = getattr(response, 'headers', None)
        content_length = headers.get('Content-Length') if headers else None

        verify_file(tmp_path, url, total_bytes, content_length, is_gzip=is_gzip)
        os.replace(tmp_path, dest_path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

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
                raise ValueError(f'problem accessing {url}: HTTP {r.status}')
            _stream_to_file(r, path, url)
        finally:
            r.release_conn()
    finally:
        http.clear()
