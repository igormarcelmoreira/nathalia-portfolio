"""Gera HTML autocontido de cada página (desktop 1440 + mobile 390 lado a lado) para importar no Figma.

Imagens e fontes viram data URIs, vídeos viram um quadro estático, media queries são
resolvidas para cada largura. Saída: figma/<pagina>.html

Uso: python tools/figma_export.py   (precisa do site já gerado em site/)
"""
import functools
import http.server
import os
import re
import threading

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
OUT = os.path.join(ROOT, "figma")
PAGES = ["index", "sobre", "projetos", "afude", "eclipsa", "clo3d"]
PORT = 8791
FONT_NAMES = {"YAD1aFjegN8_0": "Nath Mono", "YAFyGr-8pmQ_0": "Nath Pixel", "YACgEZulLoA_0": "Nath Display"}

# Roda dentro da página: devolve {css, html} da parte (.desk ou .mob) visível na largura atual.
SERIALIZE = r"""async ([part, width]) => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const root = document.querySelector(part);
  root.querySelectorAll('img[loading]').forEach(i => i.loading = 'eager');
  root.querySelectorAll('img[data-src]').forEach(i => { i.src = i.dataset.src; });
  // espera imagens decodificadas
  await Promise.all([...root.querySelectorAll('img')].map(i => i.decode().catch(() => sleep(3000))));

  const toData = (blob) => new Promise(r => { const fr = new FileReader(); fr.onload = () => r(fr.result); fr.readAsDataURL(blob); });
  const cache = {};
  async function inlineUrl(url) {
    if (url.startsWith('data:')) return url;
    if (cache[url]) return cache[url];
    const b = await (await fetch(url)).blob();
    return (cache[url] = await toData(b));
  }
  // imagens raster: reduz para no máximo 2x o tamanho exibido
  async function rasterData(img) {
    const src = img.currentSrc || img.src;
    if (/\.svg($|\?)/.test(src) || /\.gif($|\?)/.test(src)) return inlineUrl(src);
    const r = img.getBoundingClientRect();
    const scale = Math.min(1, (Math.max(r.width, r.height, 1) * 2) / Math.max(img.naturalWidth, img.naturalHeight, 1));
    const c = document.createElement('canvas');
    c.width = Math.max(1, Math.round(img.naturalWidth * scale)); c.height = Math.max(1, Math.round(img.naturalHeight * scale));
    c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
    return /\.jpe?g($|\?)/i.test(src) ? c.toDataURL('image/jpeg', 0.85) : c.toDataURL('image/png');
  }

  // vídeos -> quadro estático
  for (const v of [...root.querySelectorAll('video')]) {
    if (!v.src && v.dataset.src) v.src = v.dataset.src;
    v.muted = true;
    await new Promise(r => { if (v.readyState >= 2) r(); else { v.onloadeddata = r; setTimeout(r, 15000); } });
    v.pause();
    await new Promise(r => { v.onseeked = r; v.currentTime = (v.duration || 4) * 0.7; setTimeout(r, 5000); });
    const c = document.createElement('canvas'); c.width = v.videoWidth || 10; c.height = v.videoHeight || 10;
    c.getContext('2d').drawImage(v, 0, 0, c.width, c.height);
    const img = document.createElement('img');
    for (const a of v.attributes) if (!['src', 'data-src', 'muted', 'loop', 'playsinline', 'autoplay', 'preload'].includes(a.name)) img.setAttribute(a.name, a.value);
    img.src = c.toDataURL('image/jpeg', 0.85);
    img.alt = v.getAttribute('aria-label') || '';
    v.replaceWith(img);
  }
  for (const img of [...root.querySelectorAll('img')]) {
    if (img.src.startsWith('data:')) continue;
    img.setAttribute('src', await rasterData(img));
    img.removeAttribute('data-src'); img.removeAttribute('loading'); img.removeAttribute('srcset');
  }

  // CSS: só regras que valem nesta largura, com url() embutidas e 100vw resolvido
  const otherPart = part === '.desk' ? '.mob' : '.desk';
  let css = '';
  async function rules(list) {
    for (const r of list) {
      if (r instanceof CSSMediaRule) { if (matchMedia(r.media.mediaText).matches) await rules(r.cssRules); continue; }
      if (r instanceof CSSStyleRule && r.selectorText.trim().startsWith(otherPart)) continue;
      let t = r.cssText;
      const urls = [...t.matchAll(/url\("([^"]+)"\)/g)].map(m => m[1]);
      for (const u of urls) {
        if (u.startsWith('#') || u.startsWith('data:')) continue;
        const abs = new URL(u, r.parentStyleSheet.href || location.href).href;
        try { t = t.split(u).join(await inlineUrl(abs)); } catch (e) {}
      }
      css += t.replace(/(\d+(?:\.\d+)?)vw\b/g, (m, n) => (n * width / 100) + 'px') + '\n';
    }
  }
  for (const s of document.styleSheets) { try { if (!s.media.mediaText || matchMedia(s.media.mediaText).matches) await rules(s.cssRules); } catch (e) {} }
  // o importador ignora -webkit-text-stroke: texto de contorno vira preenchido na cor do contorno
  // (marcado com data-outline para refazer o contorno no Figma)
  for (const el of root.querySelectorAll('*')) {
    const cs = getComputedStyle(el);
    if (parseFloat(cs.webkitTextStrokeWidth) > 0 && /rgba\(0, 0, 0, 0\)|transparent/.test(cs.webkitTextFillColor + cs.color) && el.textContent.trim()) {
      el.style.setProperty('color', cs.webkitTextStrokeColor, 'important');
      el.style.setProperty('-webkit-text-fill-color', cs.webkitTextStrokeColor, 'important');
      el.dataset.outline = cs.webkitTextStrokeWidth;
    }
  }
  root.querySelectorAll('.m-menu, script').forEach(e => e.remove());
  return { css, html: root.outerHTML };
}"""


def main():
    os.makedirs(OUT, exist_ok=True)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=SITE)
    handler.func.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        b = p.chromium.launch()
        for page in PAGES:
            parts = {}
            for part, width in ((".desk", 1440), (".mob", 390)):
                ctx = b.new_context(viewport={"width": width, "height": 900})
                pg = ctx.new_page()
                pg.goto(f"http://127.0.0.1:{PORT}/{page}.html", wait_until="networkidle")
                pg.wait_for_timeout(1500)
                parts[part] = pg.evaluate(SERIALIZE, [part, width])
                ctx.close()
            doc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>{page}</title>
<style>{parts['.desk']['css']}</style>
<style>{parts['.mob']['css']}</style>
<style>
body {{ margin: 0; padding: 40px; background: #e9e9e9; display: flex; gap: 80px; align-items: flex-start; width: max-content; }}
.frame {{ flex: none; background: #151515; }}
.frame .desk {{ display: block !important; zoom: 1 !important; --z: 1; }}
.frame .mob {{ display: block !important; }}
.frame .m-head {{ position: relative !important; }}
</style></head><body>
<div class="frame" data-name="{page} — desktop" style="width:1440px">{parts['.desk']['html']}</div>
<div class="frame" data-name="{page} — mobile" style="width:390px">{parts['.mob']['html']}</div>
</body></html>"""
            # nomes de fonte iguais aos arquivos instaláveis de figma/fonts (o Figma usa a fonte instalada)
            for old, new in FONT_NAMES.items():
                doc = doc.replace(f'"{old}"', f'"{new}"').replace(old, f'"{new}"')
            path = os.path.join(OUT, page + ".html")
            open(path, "w", encoding="utf-8").write(doc)
            print(page, round(os.path.getsize(path) / 1e6, 1), "MB")
        b.close()
    srv.shutdown()


if __name__ == "__main__":
    main()
