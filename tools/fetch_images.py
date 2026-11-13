"""Download the original images listed in projects_data.py into a folder outside the repo.

Usage: python tools/fetch_images.py RAW_DIR
Files are saved as RAW_DIR/<slug>/<NN>.<ext>, where NN is the position in the project's media list.
"""
import sys, os, urllib.request
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
from projects_data import PROJECTS, SRC


def slug(p):
    return p["url"].split("/")[1].lower()


def jobs(raw):
    for p in PROJECTS:
        for i, m in enumerate(p["media"], 1):
            name = m[0] if isinstance(m, tuple) else m
            if name.startswith(("yt:", "adobe:")):
                continue
            ext = name.rsplit(".", 1)[1]
            yield SRC + name, os.path.join(raw, slug(p), "%02d.%s" % (i, ext))


def get(job):
    url, dest = job
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest, "cached"
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
        f.write(r.read())
    return dest, "ok"


if __name__ == "__main__":
    raw = sys.argv[1]
    with ThreadPoolExecutor(6) as ex:
        for dest, status in ex.map(get, list(jobs(raw))):
            print(status, dest)
