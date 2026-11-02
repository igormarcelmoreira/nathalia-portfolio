async () => {
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  // scroll everything to trigger lazy loading
  const scrollers = [...document.querySelectorAll('*')].filter(e => {
    const s = getComputedStyle(e);
    return (s.overflowY === 'auto' || s.overflowY === 'scroll') && e.scrollHeight > e.clientHeight + 10;
  });
  const sc = scrollers[0] || document.scrollingElement;
  for (let y = 0; y < sc.scrollHeight; y += 400) { sc.scrollTop = y; await sleep(120); }
  sc.scrollTop = 0; await sleep(1500);

  const blobs = {};
  async function blobToB64(url) {
    if (blobs[url]) return;
    try {
      const b = await (await fetch(url)).blob();
      const buf = new Uint8Array(await b.arrayBuffer());
      let s = ''; for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
      blobs[url] = { type: b.type, b64: btoa(s) };
    } catch (e) { blobs[url] = { err: String(e) }; }
  }

  const isEl = (e) => e.classList && e.classList.contains('DF_utQ');
  // neutralize rotations so measurements are in local (unrotated) space
  const all = [...document.querySelectorAll('.DF_utQ')];
  const saved = all.map(e => e.style.transform);
  const parseT = (t) => {
    const m = /translate\(([-\d.e]+)px,\s*([-\d.e]+)px\)/.exec(t) || [0, 0, 0];
    const r = /rotate\(([-\d.e]+)deg\)/.exec(t);
    const rest = t.replace(/translate\([^)]*\)/, '').replace(/rotate\([^)]*\)/, '').trim();
    return { x: +m[1], y: +m[2], rot: r ? +r[1] : 0, extra: rest };
  };
  all.forEach(e => { e.style.transform = e.style.transform.replace(/rotate\([^)]*\)/, 'rotate(0deg)'); });
  // also neutralize inner wrappers transforms that rotate
  await sleep(50);

  const pick = (s, keys) => Object.fromEntries(keys.map(k => [k, s.getPropertyValue(k)]));
  const TXT = ['font-family', 'font-size', 'font-weight', 'font-style', 'color', 'letter-spacing', 'line-height', 'text-decoration-line', 'text-transform', '-webkit-text-stroke', 'text-shadow', 'background-color'];

  function rel(el, frame) {
    const a = el.getBoundingClientRect(), b = frame.getBoundingClientRect();
    return { x: a.x - b.x, y: a.y - b.y, w: a.width, h: a.height };
  }
  function ownDescendants(root, sel) {
    return [...root.querySelectorAll(sel)].filter(n => n.closest('.DF_utQ') === root);
  }

  const pendingBlobs = [];
  function node(el) {
    const t = parseT(el.style.transform);
    t.rot = parseT(saved[all.indexOf(el)]).rot;
    const cs = getComputedStyle(el);
    const o = { x: t.x, y: t.y, w: parseFloat(el.style.width), h: parseFloat(el.style.height), rot: t.rot, extra: t.extra, opacity: cs.opacity };
    // nested elements
    const kids = [...el.querySelectorAll('.DF_utQ')].filter(k => k.parentElement.closest('.DF_utQ') === el);
    if (kids.length) o.children = kids.map(node);
    // anchor
    const a = el.closest('a') || el.querySelector('a');
    if (a && (!a.closest('.DF_utQ') || a.closest('.DF_utQ') === el || el.contains(a))) o.href = a.getAttribute('href');
    // text
    const ps = ownDescendants(el, 'p, li');
    if (ps.length) {
      o.text = ps.map(p => {
        const ps_ = getComputedStyle(p);
        return {
          tag: p.tagName, align: ps_.textAlign, lh: ps_.lineHeight, ls: ps_.letterSpacing, mt: ps_.marginTop, mb: ps_.marginBottom,
          listStyle: p.tagName === 'LI' ? getComputedStyle(p.parentElement).listStyleType : undefined,
          runs: (() => {
            const out = []; const w = document.createTreeWalker(p, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
            let n; while ((n = w.nextNode())) {
              if (n.nodeType === 1 && n.tagName === 'BR') { out.push({ t: '\n', s: out.length ? out[out.length - 1].s : pick(getComputedStyle(p), TXT) }); continue; }
              if (n.nodeType !== 3 || !n.data) continue;
              const par = n.parentElement; const a = par.closest('a');
              out.push({ t: n.data, s: pick(getComputedStyle(par), TXT), href: a ? a.getAttribute('href') : undefined });
            }
            return out;
          })()
        };
      });
      // Canva escala o bloco de texto com transform: scale(); guardamos largura e escala reais
      let sw = ps[0].parentElement, scaleEl = null;
      while (sw && sw !== el) { if (/scale\(/.test(sw.style.transform || '')) { scaleEl = sw; break; } sw = sw.parentElement; }
      if (scaleEl) {
        const m = /scale\(([-\d.e]+)/.exec(scaleEl.style.transform); const r = rel(scaleEl, el);
        o.textBox = { x: r.x, y: r.y, w: parseFloat(scaleEl.style.width), h: parseFloat(scaleEl.style.height), scale: +m[1], wm: scaleEl.style.writingMode };
      } else { o.textBox = rel(ps[0].parentElement, el); o.textBox.scale = 1; }
    }
    // images
    const imgs = ownDescendants(el, 'img');
    if (imgs.length) o.imgs = imgs.map(i => {
      const src = i.currentSrc || i.src; if (src.startsWith('blob:')) pendingBlobs.push(src);
      // clip from frame ancestors
      let clip = null, radius = null, p = i.parentElement;
      while (p && p !== el) { const s = getComputedStyle(p); if (s.clipPath !== 'none') clip = s.clipPath; if (s.borderRadius !== '0px') radius = s.borderRadius; p = p.parentElement; }
      const is = getComputedStyle(i);
      return { src, r: rel(i, el), tf: is.transform, filter: is.filter, opacity: is.opacity, clip, radius, nat: [i.naturalWidth, i.naturalHeight] };
    });
    const vids = ownDescendants(el, 'video');
    if (vids.length) o.videos = vids.map(v => ({ src: v.currentSrc || v.src, poster: v.poster, r: rel(v, el), loop: v.loop, muted: v.muted, autoplay: v.autoplay, sources: [...v.querySelectorAll('source')].map(s => s.src) }));
    const svgs = ownDescendants(el, 'svg').filter(s => !s.parentElement.closest('svg'));
    if (svgs.length) o.svgs = svgs.map(s => ({ html: s.outerHTML, r: rel(s, el) }));
    // colored boxes
    const boxes = ownDescendants(el, 'div').filter(d => { const s = getComputedStyle(d); return s.backgroundColor !== 'rgba(0, 0, 0, 0)' || s.backgroundImage !== 'none'; });
    if (boxes.length) o.boxes = boxes.map(d => { const s = getComputedStyle(d); return { bg: s.backgroundColor, bgi: s.backgroundImage, radius: s.borderRadius, r: rel(d, el) }; });
    return o;
  }

  const sections = [...document.querySelectorAll('section')].map(sec => {
    const canvas = sec.querySelector('._mXnjA') || sec;
    const top = [...canvas.querySelectorAll('.DF_utQ')].filter(k => !k.parentElement.closest('.DF_utQ'));
    const bgEl = sec.querySelector('.GDnEHQ');
    const sr = sec.getBoundingClientRect();
    // section background media (img/video not inside elements)
    const bgMedia = [...sec.querySelectorAll('img,video')].filter(m => !m.closest('.DF_utQ')).map(m => { const s = m.currentSrc || m.src; if (s.startsWith('blob:')) pendingBlobs.push(s); return { tag: m.tagName, src: s, poster: m.poster, r: rel(m, sec) }; });
    // fundo real da seção: últimos divs com fundo fora dos elementos
    const fills = [...sec.querySelectorAll('div')].filter(d => !d.closest('.DF_utQ') && d !== bgEl).map(d => getComputedStyle(d)).filter(s => s.backgroundColor !== 'rgba(0, 0, 0, 0)' || s.backgroundImage !== 'none').map(s => ({ bg: s.backgroundColor, bgi: s.backgroundImage }));
    const els = top.map(t => {
      const o = node(t); const clips = []; let p = t.parentElement;
      while (p && p !== canvas) { const c = getComputedStyle(p).clipPath; if (c && c !== 'none') clips.push(c); p = p.parentElement; }
      if (clips.length) o.wrapClip = clips; return o;
    });
    return { id: sec.id, w: sr.width, h: sr.height, bg: bgEl ? getComputedStyle(bgEl).backgroundColor : null, fills, bgMedia, els };
  });
  all.forEach((e, i) => e.style.transform = saved[i]);
  for (const b of pendingBlobs) await blobToB64(b);
  return { title: document.title, hash: location.hash, vw: innerWidth, sections, blobs };
}
