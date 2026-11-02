"""Monta o site em site/.

Desktop: snapshot do layout renderizado pelo Canva (extracao/snap/<pagina>.json),
com cada seção numa "tela" de 1440px escalada para a largura da janela.
Mobile: markup próprio, escrito à mão em src/mobile/<pagina>.html.

Uso: python tools/build.py
"""
import json
import os
import re
import shutil

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAP = os.path.join(ROOT, "extracao", "snap")
RAW_ASSETS = os.path.join(ROOT, "extracao")
SRC = os.path.join(ROOT, "src")
OUT = os.path.join(ROOT, "site")

PAGES = [
    # slug, arquivo, título
    ("home", "index.html", "Nathalia Dutra — fashion & design portfolio"),
    ("sobre", "sobre.html", "Sobre mim — Nathalia Dutra"),
    ("projetos", "projetos.html", "Projetos — Nathalia Dutra"),
    ("afude", "afude.html", "Afude — Nathalia Dutra"),
    ("eclipsa", "eclipsa.html", "Eclipsa — Nathalia Dutra"),
    ("clo3d", "clo3d.html", "Clo 3D — Nathalia Dutra"),
]

# ids de página/seção do Canva -> destino no novo site
LINKS = {
    "page-1": "index.html", "page-e": "index.html", "page-0": "index.html#s-0",
    "page-2": "sobre.html",
    "page-3": "projetos.html",
    "page-6": "afude.html", "page-4": "afude.html#s-4", "page-5": "afude.html#s-5",
    "page-b": "eclipsa.html", "page-7": "eclipsa.html#s-7", "page-8": "eclipsa.html#s-8",
    "page-9": "eclipsa.html#s-9", "page-a": "eclipsa.html#s-a",
    "page-c": "clo3d.html",
}

used_assets = set()


def localize(text):
    """Troca caminhos _assets/... por assets/... e registra o que foi usado."""
    def rep(m):
        used_assets.add((m.group(1), m.group(2)))
        return f"assets/{m.group(1)}/{m.group(2)}"
    return re.sub(r"(?<![\w/])_assets/(\w+)/([\w.]+)", rep, text)


def defer_media(h):
    """No desktop as mídias só carregam via JS (main.js), e só se a tela for desktop."""
    h = h.replace(' loading="lazy"', "")
    h = re.sub(r'<(img|video)([^>]*?) src="', r'<\1\2 data-src="', h)
    return h.replace(" autoplay", "")


def fix_links(h):
    def rep(m):
        href = m.group(1)
        if href.startswith("#"):
            return f'href="{LINKS.get(href[1:], "index.html")}"'
        if href.startswith("http"):
            return f'href="{href}" target="_blank" rel="noopener"'
        return m.group(0)
    return re.sub(r'href="([^"]*)"', rep, h)


# ---------------- mobile: trechos compartilhados ----------------
CTL = ('<svg class="win__ctl" viewBox="0 0 54 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2">'
       '<path d="M1 14h12"/><rect x="21" y="2" width="12" height="12"/><path d="M21 4h12" stroke-width="4"/>'
       '<path d="M41 2l12 12M53 2L41 14"/></svg>')

NAV = [("home", "index.html", "Home"), ("projetos", "projetos.html", "Projetos"),
       ("sobre", "sobre.html", "Sobre mim"), ("contato", "#contato", "Contato")]

SECTION_OF = {"afude": "projetos", "eclipsa": "projetos", "clo3d": "projetos"}


def head(slug):
    cur = SECTION_OF.get(slug, slug)
    current = ' aria-current="page"'
    items = "".join(
        f'<li><a href="{href}"{current if key == cur else ""}>{label}</a></li>'
        for key, href, label in NAV)
    return f"""<header class="m-head">
  <a class="m-logo" href="index.html"><img src="assets/media/80a34262c17f4cd8f8ec8896c11dc454.png" alt=""><span>nathalia dutra</span></a>
  <button class="m-menu-btn" type="button" aria-expanded="false" aria-controls="m-menu" aria-label="Menu">
    <svg class="bars" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 5h18v3H3zM3 11h18v3H3zM3 17h18v3H3z" fill="currentColor"/></svg>
    <svg class="x" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 3l16 16-2 2L3 5zM19 3l2 2L5 21l-2-2z" fill="currentColor"/></svg>
  </button>
</header>
<nav class="m-menu" id="m-menu" aria-label="Principal"><ul>{items}</ul></nav>"""


FOOT = """<footer class="m-foot" id="contato">
  <h2 class="m-pixel m-outline">entre em contato</h2>
  <address>
    <a href="mailto:nathalia.dutra.ribeiro@gmail.com">nathalia.dutra.ribeiro@gmail.com</a><br>
    <a href="tel:+5551997935122">+55 51 997935122</a>
  </address>
  <div class="m-social">
    <a href="https://www.linkedin.com/in/nathalia-dutra-05b0a0243" target="_blank" rel="noopener" aria-label="LinkedIn"><img src="assets/blob/84be3b50071f080b.svg" alt=""></a>
  </div>
  <img class="m-phone" src="assets/media/fa36876dabc850d6c1bc70252ccd6127.png" alt="" loading="lazy">
  <small>© Nathalia Dutra</small>
</footer>"""

# recortes de imagens que no Canva vinham de sprites
CROPS = {
    "coreldraw.png": ("media/47772a9ddd71f63a4576fc757ef65417.png", (541, 61, 749, 259)),
    "audaces-encaixes.png": ("media/46f69a080a798534fe8014dd7fd7c344.png", (30, 30, 390, 370)),
    "audaces-moldes.png": ("media/46f69a080a798534fe8014dd7fd7c344.png", (410, 30, 770, 370)),
}
MAX_W = 1000


def mobile_assets(h):
    """Versões leves (WebP, até 1000px) das imagens do mobile + width/height reais."""
    mdir = os.path.join(OUT, "assets", "m")
    os.makedirs(mdir, exist_ok=True)

    def img_tag(m):
        tag = m.group(0)
        src = re.search(r'src="assets/([^"]+)"', tag)
        if not src:
            return tag
        rel = src.group(1)
        if rel.startswith("m/"):
            name = rel[2:]
            dst = os.path.join(mdir, name)
            if not os.path.exists(dst):
                srcf, box = CROPS[name]
                Image.open(os.path.join(RAW_ASSETS, "_assets", srcf)).crop(box).save(dst)
            new = "assets/m/" + name
        elif rel.endswith((".jpg", ".png")):
            kind, fname = rel.split("/", 1)
            used_assets.add((kind, fname))  # mantém o original disponível
            name = os.path.splitext(fname)[0] + ".webp"
            dst = os.path.join(mdir, name)
            if not os.path.exists(dst):
                im = Image.open(os.path.join(RAW_ASSETS, "_assets", kind, fname))
                im = im.convert("RGBA") if im.mode in ("P", "LA", "RGBA", "L") else im.convert("RGB")
                if im.width > MAX_W:
                    im = im.resize((MAX_W, round(im.height * MAX_W / im.width)), Image.LANCZOS)
                im.save(dst, "WEBP", quality=80, method=6)
            new = "assets/m/" + name
        else:
            return tag
        w, hgt = Image.open(os.path.join(OUT, new)).size
        tag = tag.replace(src.group(0), f'src="{new}"')
        tag = re.sub(r'\s(width|height)="\d+"', "", tag)
        return tag.replace("<img", f'<img width="{w}" height="{hgt}"', 1)

    return re.sub(r"<img\b[^>]*>", img_tag, h)


def render_mobile(slug, h):
    h = h.replace(f"<!--#head:{slug}-->", head(slug)).replace("<!--#foot-->", FOOT).replace("<!--#ctl-->", CTL)
    return mobile_assets(h)


TEMPLATE = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="Portfólio de moda e design gráfico de Nathalia Dutra.">
<link rel="stylesheet" href="css/style.css">
<link rel="stylesheet" href="css/desk-{slug}.css" media="(min-width: 901px)">
</head>
<body class="p-{slug}">
<!-- DESKTOP: gerado por tools/build.py a partir do layout do Canva. Não editar à mão. -->
<div class="desk">
{desktop}
</div>
<!-- MOBILE: src/mobile/{slug}.html -->
<div class="mob">
{mobile}
</div>
<script src="js/main.js"></script>
</body>
</html>
"""


def main():
    os.makedirs(os.path.join(OUT, "css"), exist_ok=True)
    for slug, fname, title in PAGES:
        snap = json.load(open(os.path.join(SNAP, slug + ".json"), encoding="utf-8"))
        desktop = "\n".join(defer_media(fix_links(localize(s["html"]))) for s in snap["sections"])
        # as classes geradas são por página; prefixamos com .desk para não vazar no mobile
        css = "\n".join(".desk " + line for line in localize(snap["css"]).splitlines())
        open(os.path.join(OUT, "css", f"desk-{slug}.css"), "w", encoding="utf-8").write(css)
        mpath = os.path.join(SRC, "mobile", slug + ".html")
        mobile = open(mpath, encoding="utf-8").read() if os.path.exists(mpath) else ""
        mobile = render_mobile(slug, mobile)
        for m in re.finditer(r'assets/(media|blob|video|fonts)/([\w.]+)', mobile):
            used_assets.add((m.group(1), m.group(2)))
        css_text = open(os.path.join(SRC, "css", "style.css"), encoding="utf-8").read()
        for m in re.finditer(r'assets/(media|blob|video|fonts)/([\w.]+)', css_text):
            used_assets.add((m.group(1), m.group(2)))
        open(os.path.join(OUT, fname), "w", encoding="utf-8").write(
            TEMPLATE.format(title=title, slug=slug, desktop=desktop, mobile=mobile))
        print("ok", fname)
    for d in ("css", "js"):
        if os.path.isdir(os.path.join(SRC, d)):
            shutil.copytree(os.path.join(SRC, d), os.path.join(OUT, d), dirs_exist_ok=True)
    shutil.copy2(os.path.join(SRC, "vercel.json"), os.path.join(OUT, "vercel.json"))
    for f in os.listdir(os.path.join(RAW_ASSETS, "_assets", "fonts")):
        used_assets.add(("fonts", f))
    for kind, name in sorted(used_assets):
        src = os.path.join(RAW_ASSETS, "_assets", kind, name)
        dst = os.path.join(OUT, "assets", kind, name)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(src):
            if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
                shutil.copy2(src, dst)
        else:
            print("FALTANDO", kind, name)
    print(len(used_assets), "assets")


if __name__ == "__main__":
    main()
