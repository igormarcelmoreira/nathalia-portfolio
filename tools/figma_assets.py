"""Prepara figma/upload/: as imagens do layout mobile com nomes legíveis, prontas para subir no Figma.
Vídeos viram uma capa (PNG de um quadro do meio do vídeo). Uso: python tools/figma_assets.py"""
import functools
import http.server
import os
import re
import shutil
import sys
import threading

from PIL import Image
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_kit import KIT  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
OUT = os.path.join(ROOT, "figma", "upload")
_all = [n for items in KIT.values() for n in items.values()]
# nomes repetidos entre pastas (ex.: desenho-vestido na 90's e na Viúva) ganham o nome da pasta na frente
NAMES = {p: (n if _all.count(n) == 1 else folder.split("/")[-1] + "-" + n)
         for folder, items in KIT.items() for p, n in items.items()}
NAMES.update({"coreldraw": "coreldraw", "audaces-moldes": "audaces-moldes", "audaces-encaixes": "audaces-encaixes",
              "e8baf23f": "lupa", "f7a12c75": "lupa-2"})


def readable(path):
    base = os.path.splitext(os.path.basename(path))[0]
    for p, n in NAMES.items():
        if base.startswith(p):
            return n
    return base


def mobile_sources():
    srcs = []
    for p in ["index", "sobre", "projetos", "afude", "eclipsa", "clo3d"]:
        h = open(os.path.join(SITE, p + ".html"), encoding="utf-8").read()
        for m in re.finditer(r'src="(assets/[^"]+)"', h[h.index('<div class="mob">'):]):
            if m.group(1) not in srcs:
                srcs.append(m.group(1))
    css = open(os.path.join(SITE, "css", "style.css"), encoding="utf-8").read()
    for m in re.finditer(r'url\("\.\./(assets/(?:media|blob)/[^"]+)"\)', css):
        if m.group(1) not in srcs:
            srcs.append(m.group(1))
    return srcs


POSTER = r"""async (src) => {
  const v = document.createElement('video'); v.muted = true; v.src = src; document.body.appendChild(v);
  await new Promise(r => { v.onloadeddata = r; setTimeout(r, 15000); });
  await new Promise(r => { v.onseeked = r; v.currentTime = v.duration * 0.45; setTimeout(r, 8000); });
  const c = document.createElement('canvas'); c.width = v.videoWidth; c.height = v.videoHeight;
  c.getContext('2d').drawImage(v, 0, 0);
  return c.toDataURL('image/jpeg', 0.85);
}"""


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    srcs = mobile_sources()
    videos = []
    for s in srcs:
        name = readable(s)
        ext = os.path.splitext(s)[1]
        if ext == ".mp4":
            videos.append((s, name))
        elif ext == ".gif":
            Image.open(os.path.join(SITE, s)).convert("RGBA").save(os.path.join(OUT, name + ".png"))
        else:
            shutil.copy2(os.path.join(SITE, s), os.path.join(OUT, name + ext))
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=SITE)
    handler.func.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8792), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    import base64
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto("http://127.0.0.1:8792/index.html")
        for s, name in videos:
            data = pg.evaluate(POSTER, s)
            open(os.path.join(OUT, name + "-capa.jpg"), "wb").write(base64.b64decode(data.split(",", 1)[1]))
        b.close()
    srv.shutdown()
    for f in sorted(os.listdir(OUT)):
        print(f)


if __name__ == "__main__":
    main()
