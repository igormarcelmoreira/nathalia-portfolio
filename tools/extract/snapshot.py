import base64, hashlib, json, os, re, sys
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "extracao")
JS = open(os.path.join(HERE, "snapshot.js"), encoding="utf-8").read()
BASE = "https://gibbon-d2by24.my.canva.site/"
EXT = {"image/svg+xml": "svg", "image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "image/gif": "gif", "video/mp4": "mp4"}
PAGES = {"home": "page-1", "sobre": "page-2", "projetos": "page-3", "afude": "page-6", "eclipsa": "page-b", "clo3d": "page-c"}
os.makedirs(os.path.join(OUT, "_assets", "blob"), exist_ok=True)
os.makedirs(os.path.join(OUT, "snap"), exist_ok=True)
want = sys.argv[1:] or list(PAGES)
with sync_playwright() as p:
    b = p.chromium.launch()
    for slug in want:
        ctx = b.new_context(viewport={"width": 1440, "height": 900})
        pg = ctx.new_page()
        pg.goto(BASE + "#" + PAGES[slug], wait_until="networkidle")
        pg.wait_for_timeout(3000)
        data = pg.evaluate(JS)
        mapping = {}
        for url, bl in data.pop("blobs").items():
            if "b64" not in bl: print("blob err", url, bl); continue
            raw = base64.b64decode(bl["b64"])
            name = hashlib.sha1(raw).hexdigest()[:16] + "." + EXT.get(bl["type"], "bin")
            open(os.path.join(OUT, "_assets", "blob", name), "wb").write(raw)
            mapping[url] = "_assets/blob/" + name
        s = json.dumps(data, ensure_ascii=False)
        for url, local in mapping.items(): s = s.replace(url, local)
        s = s.replace(BASE, "")
        open(os.path.join(OUT, "snap", slug + ".json"), "w", encoding="utf-8").write(s)
        print(slug, data["title"], len(data["sections"]), len(s) // 1024, "KB")
        ctx.close()
    b.close()
