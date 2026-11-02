import base64, hashlib, json, os, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "extracao")
JS = open(os.path.join(HERE, "extract.js"), encoding="utf-8").read()
BASE = "https://gibbon-d2by24.my.canva.site/"
EXT = {"image/svg+xml": "svg", "image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "image/gif": "gif"}

os.makedirs(os.path.join(OUT, "_assets", "blob"), exist_ok=True)
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
os.makedirs(os.path.join(OUT, "ref"), exist_ok=True)

hashes = sys.argv[1:] or ["page-1", "page-2", "page-3", "page-4", "page-7", "page-c"]
seen = {}
with sync_playwright() as p:
    b = p.chromium.launch()
    for h in hashes:
        ctx = b.new_context(viewport={"width": 1440, "height": 900})
        pg = ctx.new_page()
        pg.goto(BASE + "#" + h, wait_until="networkidle")
        pg.wait_for_timeout(3000)
        data = pg.evaluate(JS)
        key = data["title"] + "|" + ",".join(s["id"] for s in data["sections"])
        if key in seen:
            print(h, "duplicate of", seen[key]); ctx.close(); continue
        seen[key] = h
        mapping = {}
        for url, bl in data.pop("blobs").items():
            if "b64" not in bl: continue
            raw = base64.b64decode(bl["b64"])
            name = hashlib.sha1(raw).hexdigest()[:16] + "." + EXT.get(bl["type"], "bin")
            open(os.path.join(OUT, "_assets", "blob", name), "wb").write(raw)
            mapping[url] = "_assets/blob/" + name
        s = json.dumps(data, ensure_ascii=False)
        for url, local in mapping.items(): s = s.replace(url, local)
        s = s.replace(BASE, "")
        open(os.path.join(OUT, "data", h + ".json"), "w", encoding="utf-8").write(s)
        total = int(sum(x["h"] for x in data["sections"])) + 40
        pg.set_viewport_size({"width": 1440, "height": min(total, 16000)})
        pg.wait_for_timeout(2500)
        pg.screenshot(path=os.path.join(OUT, "ref", h + ".png"))
        print(h, data["title"], len(data["sections"]), "sections", total, "px")
        ctx.close()
    b.close()
