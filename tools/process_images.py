"""Turn the downloaded originals into web-sized WebP files in images/work/<slug>/NN.webp.

- Wide images are shrunk to at most 1600 px wide.
- Small images are enlarged (up to 3x, to about 1400 px wide) with a high-quality resize and a light sharpen,
  so they stay as crisp as a small source can be. This cannot add detail that was never there.
- Animated GIFs become animated WebP at their own size (not enlarged).

Usage: python tools/process_images.py RAW_DIR
"""
import sys, os, glob
from PIL import Image, ImageFilter, ImageSequence

MAX_W, TARGET_W, MAX_UP = 1600, 1400, 3.0
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def new_size(w, h, animated=False):
    if animated and w <= MAX_W:
        f = 1  # moving images keep their size, enlarging them makes the files huge
    elif w > MAX_W:
        f = MAX_W / w
    elif w < TARGET_W:
        f = min(MAX_UP, TARGET_W / w)
    else:
        f = 1
    return max(1, round(w * f)), max(1, round(h * f)), f


def fix(im, f, animated=False):
    w, h, _ = new_size(*im.size, animated)
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA" if ("A" in im.getbands() or im.info.get("transparency") is not None) else "RGB")
    if (w, h) != im.size:
        im = im.resize((w, h), Image.LANCZOS)
        if f > 1:
            im = im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))
    return im


def run(raw):
    out_files = 0
    for src in sorted(glob.glob(os.path.join(raw, "*", "*"))):
        slug = os.path.basename(os.path.dirname(src))
        num = os.path.splitext(os.path.basename(src))[0]
        dest_dir = os.path.join(ROOT, "images", "work", slug)
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, num + ".webp")
        im = Image.open(src)
        animated = getattr(im, "is_animated", False) and im.n_frames > 1
        f = new_size(*im.size, animated)[2]
        if animated:
            frames, durs = [], []
            for fr in ImageSequence.Iterator(im):
                durs.append(fr.info.get("duration", 100))
                frames.append(fix(fr.convert("RGBA"), f, True))
            frames[0].save(dest, "WEBP", save_all=True, append_images=frames[1:], duration=durs, loop=0, quality=75, method=4)
        else:
            im.load()
            fix(im, f).save(dest, "WEBP", quality=82, method=6)
        out_files += 1
        print(slug, num, im.size, "->", Image.open(dest).size, os.path.getsize(dest) // 1024, "KB")
    print(out_files, "files written")


if __name__ == "__main__":
    run(sys.argv[1])
