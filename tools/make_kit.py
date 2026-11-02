"""Monta kit-nathalia/: todos os assets do site com nomes legíveis, por página, + fontes,
textos e referências. Uso: python tools/make_kit.py"""
import glob
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "extracao", "_assets")
OUT = os.path.join(ROOT, "kit-nathalia")

# prefixo do arquivo extraído -> destino legível
KIT = {
    "00-elementos-gerais": {
        "80a34262": "computador-pixel", "26d55e05": "estrela-cromada", "fa36876d": "celular-flip",
        "d2ce9ffb": "fundo-xadrez", "1759b1a5": "pasta-rosa", "74360953": "pasta-verde",
        "e8baf23f": "lupa", "84be3b50": "icone-linkedin", "99d3cecf": "icone-instagram",
        "a4da0048": "icone-globo", "9ce30feb": "seta", "191d0154": "icone-arquivo-verde",
        "c863a1f1": "cursor-animado", "1c7878e0": "botao-start", "38bc6c44": "moldura-polaroid",
        "58903fb1": "moldura-filme",
    },
    "01-janelas-retro": {
        "4d4bcbf9": "janela-paint", "7f93df7e": "janela-textedit", "6b61301a": "janela-idiomas",
        "cc394233": "barra-idioma", "f29509a3": "controles-janela-ciano", "6a01b9ba": "controles-janela-azul",
        "033ba6f9": "controles-janela-rosa", "b4b1b0ff": "controles-janela-azul-2",
        "4026045b": "controles-janela-xp", "8afe6d10": "controles-janela-vermelho",
    },
    "02-home": {"d97ae158": "foto-nath-maos-no-rosto"},
    "03-sobre": {
        "2f3f609f": "foto-deserto", "53b7ebdf": "foto-selfie-campo",
        "54f79a77": "letra-n", "3249198f": "letra-a", "8be4095d": "letra-t", "332911a8": "letra-h",
    },
    "03-sobre/icones-apps": {
        "eed949ee": "photoshop", "d059cc47": "illustrator", "09aca1e1": "lightroom", "e85cd550": "figma",
        "d43c721e": "capcut", "abf5a785": "clo3d", "47772a9d": "todos-os-apps-grade",
        "46f69a08": "audaces-moldes-e-encaixes",
    },
    "04-projetos": {"97ec0f4f": "fundo-ceu-campo"},
    "05-afude/identidade-visual": {
        "308a8521": "cartoes", "db4fe7e9": "adesivo-sol", "1317b7d0": "adesivo-gato",
        "7fff8c26": "adesivo-bebe", "31815024": "tag-logo", "d78b5000": "tag-estrelas", "5bbf177c": "tag-upcycle",
        "adf1f037": "video-embalagem",
    },
    "05-afude/site-e-redes": {
        "e703149f": "video-site", "7607e276": "video-instagram",
        "0ded808c": "video-post-upcycle", "eb13b95e": "video-post-drop",
    },
    "05-afude/drop-o-que-os-olhos-nao-veem": {
        "fbb31167": "01-porta-vermelha-bolsa", "9a93132a": "02-bolsa-coracao", "08aef9d5": "03-camiseta-colar",
        "c43a1567": "04-rua-camiseta-coracao", "5929f9fe": "05-duas-modelos", "e5adb13b": "06-escada-ecobag",
        "c4d8d74a": "07-camiseta-marrom", "09974c84": "08-ecobag-estrela", "2e27f1f3": "09-cropped-marrom",
    },
    "06-eclipsa": {"1301b8d3": "video-grade-posts"},
    "06-eclipsa/basicos-up": {"f4ec20ea": "01-jaqueta-patchwork", "51e2cb3d": "02-calca-patchwork", "d7794408": "03-top-e-short"},
    "06-eclipsa/90s-vibes": {
        "8412e011": "01-cropped-manga-bufante", "5c5ec9a7": "02-top-frente-unica", "cf34e9e6": "03-calca-xadrez",
        "2ecfb0c7": "04-vestido-xadrez",
        "b69006d0": "desenho-cropped", "3a1426b8": "desenho-calca-1", "27d1db7e": "desenho-top-frente-unica",
        "5f0cb6c8": "desenho-calca-2", "2b421531": "desenho-blusa-gola-alta", "7c290f79": "desenho-vestido",
    },
    "06-eclipsa/viuva-negra": {
        "4c2b00f6": "01-jaqueta-e-vestido", "e6e8a5ed": "02-vestido-preto", "b0f46588": "03-top-e-saia-jeans",
        "e52b5cf1": "04-top-e-cinto", "23d148e3": "05-top-tiras-e-short", "94624560": "06-jaqueta-sentada",
        "911bfe6c": "desenho-top-frente-unica", "896fb0e0": "desenho-jaqueta", "c30db840": "desenho-top-tiras",
        "5f8fa91e": "desenho-saia", "28ed7ef8": "desenho-vestido", "71c1aa21": "desenho-short",
    },
    "07-clo3d": {"06992417": "fundo-cetim-vermelho", "19fb8ab2": "video-render-3d", "a927ac44": "render-vestido"},
}


def find(prefix):
    hits = [p for p in glob.glob(os.path.join(RAW, "*", prefix + "*")) if not p.endswith(".m3u")]
    if len(hits) != 1:
        raise SystemExit(f"prefixo {prefix}: {hits}")
    return hits[0]


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    n = 0
    for folder, items in KIT.items():
        d = os.path.join(OUT, "imagens-e-videos", folder)
        os.makedirs(d, exist_ok=True)
        for prefix, name in items.items():
            src = find(prefix)
            shutil.copy2(src, os.path.join(d, name + os.path.splitext(src)[1]))
            n += 1
    # ícones que no Canva vinham recortados de uma grade
    apps = os.path.join(OUT, "imagens-e-videos", "03-sobre", "icones-apps")
    for f, name in (("coreldraw.png", "coreldraw"), ("audaces-moldes.png", "audaces-moldes"), ("audaces-encaixes.png", "audaces-encaixes")):
        shutil.copy2(os.path.join(ROOT, "site", "assets", "m", f), os.path.join(apps, name + ".png"))
        n += 1
    shutil.copytree(os.path.join(ROOT, "figma", "fonts"), os.path.join(OUT, "fontes"))
    ref = os.path.join(OUT, "referencia-site-atual")
    os.makedirs(ref)
    for f in glob.glob(os.path.join(ROOT, "extracao", "ref", "*.png")):
        if not os.path.basename(f).startswith("_"):
            shutil.copy2(f, os.path.join(ref, "desktop-" + os.path.basename(f)))
    for f in glob.glob(os.path.join(ROOT, "kit-src", "*")):
        shutil.copy2(f, OUT)
    print(n, "arquivos de mídia")


if __name__ == "__main__":
    main()
