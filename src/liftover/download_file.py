
import urllib3

def download_file(url, path):
    http = urllib3.PoolManager()
    r = http.request('GET', url, preload_content=False)
    if r.status != 200:
        raise ValueError('problem accessing ' + url)
    with open(path, 'wb') as f:
        for chunk in r.stream(1600):
            f.write(chunk)
    r.release_conn()
