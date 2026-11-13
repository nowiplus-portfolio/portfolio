"""Write one page per project into work/<slug>.html from projects_data.py.

Usage: python tools/build_projects.py
Run tools/fetch_images.py and tools/process_images.py first (they create images/work/<slug>/NN.webp).
"""
import os, sys, re
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from projects_data import PROJECTS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    DOMAIN = open(os.path.join(ROOT, "CNAME")).read().strip()
except OSError:
    DOMAIN = "nowiplus.co"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def slug(p):
    return p["url"].split("/")[1].lower()


class Linker:
    """Puts each link on the first place its words appear, in reading order."""
    def __init__(self, links):
        self.todo = [(esc(w), a) for w, a in links]

    def __call__(self, html):
        for item in list(self.todo):
            w, a = item
            if w in html:
                html = html.replace(w, '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(a), w), 1)
                self.todo.remove(item)
        return html


def rich(text, link):
    return link(esc(text)).replace("\n", "<br>")


def render_text(text, link):
    """Returns (intro_html, credits_html)."""
    intro, credits = [], ""
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.split("\n")
        if lines[0] == "::credits":
            rows = []
            for ln in lines[1:]:
                if " | " in ln:
                    k, v = ln.split(" | ", 1)
                    rows.append('<div class="row"><dt>%s</dt><dd>%s</dd></div>' % (esc(k), link(esc(v))))
                else:
                    rows.append('<div class="row solo"><dt>%s</dt></div>' % link(esc(ln)))
            credits = '<section class="credits"><h2>Credits</h2><dl>%s</dl></section>' % "".join(rows)
        elif block.strip() == "...":
            intro.append('<p class="gap" aria-hidden="true">&hellip;</p>')
        elif lines[0].startswith("## "):
            intro.append("<h2>%s</h2>" % link(esc(lines[0][3:])))
            rest = lines[1:]
            if rest and all(l.startswith("- ") for l in rest):
                intro.append("<ul>%s</ul>" % "".join("<li>%s</li>" % link(esc(l[2:])) for l in rest))
            elif rest:
                intro.append("<p>%s</p>" % rich("\n".join(rest), link))
        elif all(l.startswith("- ") for l in lines):
            intro.append("<ul>%s</ul>" % "".join("<li>%s</li>" % link(esc(l[2:])) for l in lines))
        else:
            intro.append("<p>%s</p>" % rich(block, link))
    return "\n".join(intro), credits


def media_html(p, i, m, first):
    caption = None
    if isinstance(m, tuple):
        m, caption = m
    label = "%s · %s" % (p["client"], p["what"])
    if m.startswith("yt:"):
        return ('<div class="video"><iframe src="https://www.youtube-nocookie.com/embed/%s" title="%s, video" '
                'loading="%s" allow="accelerometer; encrypted-media; gyroscope; picture-in-picture; fullscreen" allowfullscreen></iframe></div>'
                % (m[3:], esc(label), "eager" if first else "lazy"))
    if m.startswith("adobe:"):
        # Behance's own video player refuses to play outside Behance ("Api Key is invalid"),
        # so show a link to the video there. Replace this with a real player when a video file or YouTube/Vimeo link exists.
        return ('<a class="video video-link" href="https://www.behance.net/gallery/%s" target="_blank" rel="noopener">'
                '<span>Watch the video on Behance &#8599;</span></a>' % p["url"])
    rel = "images/work/%s/%02d.webp" % (slug(p), i)
    w, h = Image.open(os.path.join(ROOT, rel)).size
    img = ('<img src="../%s" width="%d" height="%d" alt="%s, image %d" %s>'
           % (rel, w, h, esc(label), i, 'fetchpriority="high"' if first else 'loading="lazy" decoding="async"'))
    if caption:
        return "<figure>%s<figcaption>%s</figcaption></figure>" % (img, esc(caption))
    return "<figure>%s</figure>" % img


def page(p, prev, nxt):
    s = slug(p)
    link = Linker(p["links"])
    desc_html = "".join("<p>%s</p>" % rich(d, link) for d in p["desc"].split("\n")) if p["desc"] else ""
    intro, credits = render_text(p["text"], link)
    items = [(i, m) for i, m in enumerate(p["media"], 1)]
    hero = media_html(p, items[0][0], items[0][1], True)
    rest = "\n".join(media_html(p, i, m, False) for i, m in items[1:])
    facts = '<li><span>Creative fields</span><span>%s</span></li>' % esc(p["fields"])
    if p["tools"]:
        facts += '<li><span>Tools</span><span>%s</span></li>' % esc(p["tools"])
    first_img = next(i for i, m in items if not (m[0] if isinstance(m, tuple) else m).startswith(("yt:", "adobe:")))
    og_img = "https://%s/images/work/%s/%02d.webp" % (DOMAIN, s, first_img)
    summary = (p["desc"].split("\n")[0] if p["desc"] else "%s: %s by Nowi Plus." % (p["client"], p["what"]))
    title = "%s · %s | Nowi Plus" % (p["client"], p["what"])
    nav = ""
    if prev:
        nav += '<a class="prev" href="%s.html"><span class="label">Previous</span><b>%s</b></a>' % (slug(prev), esc(prev["client"]))
    if nxt:
        nav += '<a class="next" href="%s.html"><span class="label">Next</span><b>%s</b></a>' % (slug(nxt), esc(nxt["client"]))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(summary)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(summary)}">
<meta property="og:type" content="article">
<meta property="og:image" content="{og_img}">
<link rel="canonical" href="https://{DOMAIN}/work/{s}.html">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900&family=Climate+Crisis&family=Hanken+Grotesk:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="project.css">
</head>
<body>

<header class="top">
  <div class="wrap">
    <a class="mark" href="../index.html">Nowi<span>+</span></a>
    <nav aria-label="Main">
      <a href="../index.html#work">Work</a>
      <a href="../index.html#about" class="hide-s">About</a>
      <a href="../index.html#contact">Contact</a>
    </nav>
  </div>
</header>

<main>
  <article class="project">
    <div class="wrap">
      <a class="back" href="../index.html#work">&larr; All work</a>
      <div class="head">
        <span class="label">{esc(p["sector"])}</span>
        <h1>{esc(p["client"])}</h1>
        <p class="what">{esc(p["what"])}</p>
        <div class="lede">{desc_html}</div>
        <ul class="facts">{facts}</ul>
      </div>
    </div>
    <div class="wrap col">
      {hero}
    </div>
    <div class="wrap col">
      <div class="prose">
{intro}
      </div>
    </div>
    <div class="wrap col gallery">
{rest}
    </div>
    <div class="wrap col">
      {credits}
      <p class="source"><a href="https://www.behance.net/gallery/{p["url"]}" target="_blank" rel="noopener">View this project on Behance &#8599;</a></p>
    </div>
    <nav class="wrap pager" aria-label="More projects">{nav}</nav>
  </article>
</main>

<footer class="contact" id="contact">
  <div class="wrap">
    <span class="label" style="color:inherit;opacity:.8">Contact</span>
    <h2>Got a launch, a rebrand or a story to tell?</h2>
    <div class="row">
      <a class="email" href="mailto:work@nowiplus.co">work@nowiplus.co</a>
    </div>
    <div class="social">
      <a href="https://www.linkedin.com/in/nowiplus/" target="_blank" rel="noopener">LinkedIn &#8599;</a>
      <a href="https://instagram.com/nowiplus" target="_blank" rel="noopener">Instagram &#8599;</a>
      <a href="https://www.behance.net/nowiplus" target="_blank" rel="noopener">Behance &#8599;</a>
    </div>
    <small>&copy; <span id="yr">2026</span> Nowi Plus &middot; Barcelona</small>
  </div>
</footer>
<script>document.getElementById("yr").textContent = new Date().getFullYear();</script>
</body>
</html>
"""


if __name__ == "__main__":
    out = os.path.join(ROOT, "work")
    os.makedirs(out, exist_ok=True)
    n = len(PROJECTS)
    for k, p in enumerate(PROJECTS):
        prev = PROJECTS[k - 1] if k > 0 else None
        nxt = PROJECTS[k + 1] if k < n - 1 else None
        with open(os.path.join(out, slug(p) + ".html"), "w", encoding="utf-8", newline="\n") as f:
            f.write(page(p, prev, nxt))
        print("wrote work/%s.html" % slug(p))
