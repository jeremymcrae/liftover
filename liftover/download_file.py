
import requests

def download_file(url, path):
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(path, 'wb') as f:
        for chunk in r.iter_content(1600):
            f.write(chunk)
