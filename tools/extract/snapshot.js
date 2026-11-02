async () => {
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  const scrollers = [...document.querySelectorAll('*')].filter(e => {
    const s = getComputedStyle(e);
    return (s.overflowY === 'auto' || s.overflowY === 'scroll') && e.scrollHeight > e.clientHeight + 10;
  });
  const sc = scrollers[0] || document.scrollingElement;
  for (let y = 0; y < sc.scrollHeight; y += 300) { sc.scrollTop = y; await sleep(150); }
  sc.scrollTop = 0; await sleep(2500);

  const PROPS = ['position', 'top', 'left', 'right', 'bottom', 'width', 'height', 'display', 'box-sizing',
    'transform', 'transform-origin', 'opacity', 'overflow-x', 'overflow-y', 'clip-path', '-webkit-mask-image', '-webkit-mask-size', '-webkit-mask-position', '-webkit-mask-repeat',
    'background-color', 'background-image', 'background-size', 'background-position', 'background-repeat', 'background-clip',
    'border-top', 'border-right', 'border-bottom', 'border-left', 'border-radius', 'box-shadow', 'filter', 'mix-blend-mode', 'z-index',
    'margin-top', 'margin-right', 'margin-bottom', 'margin-left', 'padding-top', 'padding-right', 'padding-bottom', 'padding-left',
    'flex-direction', 'align-items', 'justify-content', 'flex-grow', 'flex-shrink', 'flex-basis', 'vertical-align',
    'object-fit', 'object-position', 'visibility', 'writing-mode', 'list-style-type', 'list-style-position', 'text-indent',
    'color', 'font-family', 'font-size', 'font-weight', 'font-style', 'line-height', 'letter-spacing', 'word-spacing', 'text-align',
    'text-decoration-line', 'text-decoration-color', 'text-decoration-thickness', 'text-underline-offset', 'text-transform', 'white-space', 'overflow-wrap', 'word-break',
    '-webkit-text-stroke-width', '-webkit-text-stroke-color', '-webkit-text-fill-color', 'text-shadow', 'font-feature-settings', 'font-variant-ligatures'];
  const INHERITED = new Set(['color', 'font-family', 'font-size', 'font-weight', 'font-style', 'line-height', 'letter-spacing', 'word-spacing', 'text-align',
    'text-transform', 'white-space', 'overflow-wrap', 'word-break', '-webkit-text-stroke-width', '-webkit-text-stroke-color', '-webkit-text-fill-color', 'text-shadow',
    'visibility', 'writing-mode', 'list-style-type', 'list-style-position', 'text-indent', 'font-feature-settings', 'font-variant-ligatures']);

  // estilos padrão por tag
  const sandbox = document.createElement('div');
  sandbox.style.cssText = 'position:absolute;left:-99999px;top:0;all:initial';
  document.body.appendChild(sandbox);
  const defaults = {};
  function def(tag) {
    if (defaults[tag]) return defaults[tag];
    const el = document.createElement(tag); sandbox.appendChild(el);
    const s = getComputedStyle(el); const o = {};
    for (const p of PROPS) o[p] = s.getPropertyValue(p);
    sandbox.removeChild(el); return (defaults[tag] = o);
  }

  const blobs = {};
  const urls = new Set();
  async function grab(url) {
    if (blobs[url]) return;
    try {
      const b = await (await fetch(url)).blob();
      const buf = new Uint8Array(await b.arrayBuffer());
      let s = ''; for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
      blobs[url] = { type: b.type, b64: btoa(s) };
    } catch (e) { blobs[url] = { err: String(e) }; }
  }

  const classes = new Map(); let cn = 0;
  function cls(style) {
    if (!style) return '';
    if (!classes.has(style)) classes.set(style, 'k' + (cn++).toString(36));
    return classes.get(style);
  }
  const esc = (t) => t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const escA = (t) => esc(t).replace(/"/g, '&quot;');

  function styleOf(el, parentCS) {
    const s = getComputedStyle(el); const d = def(el.tagName.toLowerCase()); const out = [];
    const inline = s.display === 'inline';
    for (const p of PROPS) {
      let v = s.getPropertyValue(p);
      if (inline && (p === 'width' || p === 'height')) continue;
      if (INHERITED.has(p)) { if (parentCS && parentCS.getPropertyValue(p) === v) continue; }
      else if (v === d[p] && !(p === 'width' || p === 'height')) continue;
      if ((p === 'width' || p === 'height') && v === 'auto') continue;
      if (p === 'font-family') v = v.replace(/,\s*auto\b/, '');
      if (/url\("?blob:/.test(v)) v.replace(/blob:[^")]+/g, (m) => { urls.add(m); return m; });
      out.push(p + ':' + v);
    }
    return { css: out.join(';'), cs: s };
  }

  function ser(el, parentCS) {
    if (el.nodeType === 3) return esc(el.data);
    if (el.nodeType !== 1) return '';
    const tag = el.tagName.toLowerCase();
    if (['script', 'style', 'noscript', 'template', 'button'].includes(tag)) return '';
    if (tag === 'svg') {
      const s = getComputedStyle(el);
      let h = el.outerHTML.replace(/^<svg([^>]*?)\sclass="[^"]*"/, '<svg$1');
      h.replace(/blob:[^"')\s]+/g, (m) => { urls.add(m); return m; });
      const { css } = styleOf(el, parentCS);
      return h.replace(/^<svg/, '<svg class="' + cls(css) + '"');
    }
    const { css, cs } = styleOf(el, parentCS);
    if (cs.display === 'none') return '';
    let attrs = '';
    const k = cls(css); if (k) attrs += ' class="' + k + '"';
    if (tag === 'img') {
      const src = el.currentSrc || el.src; if (src.startsWith('blob:')) urls.add(src);
      attrs += ' src="' + escA(src) + '" alt="' + escA(el.alt || '') + '" loading="lazy" decoding="async"';
    } else if (tag === 'video') {
      const src = el.currentSrc || el.src; if (src.startsWith('blob:')) urls.add(src);
      attrs += ' src="' + escA(src) + '" muted loop playsinline autoplay preload="metadata"';
      return '<video' + attrs + '></video>';
    } else if (tag === 'a') {
      attrs += ' href="' + escA(el.getAttribute('href') || '') + '"';
    } else if (tag === 'section' && el.id) {
      attrs += ' id="s-' + escA(el.id) + '"';
    }
    let inner = '';
    for (const c of el.childNodes) inner += ser(c, cs);
    if (tag === 'img' || tag === 'br') return '<' + tag + attrs + '>';
    const outTag = ['p', 'span', 'a', 'ul', 'ol', 'li', 'section', 'img', 'br', 'strong', 'em', 'u'].includes(tag) ? tag : 'div';
    return '<' + outTag + attrs + '>' + inner + '</' + outTag + '>';
  }

  const sections = [...document.querySelectorAll('section')].map(sec => {
    const r = sec.getBoundingClientRect();
    // pai da seção define a cor de texto/fonte herdada; usamos o computed do pai como base
    return { id: sec.id, w: r.width, h: r.height, html: ser(sec, null) };
  });
  const css = [...classes.entries()].map(([s, k]) => '.' + k + '{' + s + '}').join('\n');
  for (const u of urls) await grab(u);
  sandbox.remove();
  return { title: document.title, sections, css, blobs };
}
