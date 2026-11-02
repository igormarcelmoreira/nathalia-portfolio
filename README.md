# Portfólio Nathalia Dutra

O site que antes estava no Canva (https://gibbon-d2by24.my.canva.site/), agora em HTML, CSS e JS puros.

- **Desktop (acima de 900px):** igual ao Canva. Cada seção é uma "tela" de 1440px, com os mesmos elementos, fontes e posições, escalada para a largura da janela.
- **Mobile (até 900px):** layout redesenhado com a mesma identidade visual (janelas retrô, pixel font, cores). Tem menu, breadcrumb, galerias com rolagem lateral e o contato no rodapé de todas as páginas.

## Estrutura

```
site/                 ← site pronto para publicar (é só subir esta pasta)
src/
  mobile/<pagina>.html  ← markup do mobile (editar aqui)
  css/style.css         ← estilos (fontes, mobile)
  js/main.js            ← zoom do desktop, carregamento de mídia, menu
tools/build.py        ← gera site/ a partir de src/ + extracao/
tools/extract/        ← scripts que capturam o site do Canva (Playwright)
extracao/
  snap/<pagina>.json    ← snapshot do layout desktop do Canva
  data/<pagina>.json    ← dados estruturados (textos, posições, estilos)
  _assets/              ← imagens, vídeos e fontes baixados do Canva
  ref/<pagina>.png      ← screenshots de referência do Canva
```

## Como gerar e testar

```bash
python tools/build.py
```

```bash
python -m http.server 8770 --directory site
```

Depois é só abrir http://127.0.0.1:8770.

O build precisa de Python 3 com Pillow (`pip install pillow`). Ele também cria versões WebP leves das imagens do mobile em `site/assets/m/`.

## Publicar (Vercel)

Site no ar: https://nathalia-dutra-nine.vercel.app (projeto `nathalia-dutra` na Vercel).

Para publicar uma atualização, rode o build e depois:

```bash
cd site && npx vercel@latest deploy --prod
```

A pasta `site/.vercel` guarda o vínculo com o projeto, então não apague `site/` inteira. O `.env.local` que a CLI cria ali não é publicado.

## Como editar

- **Textos e imagens no mobile:** edite `src/mobile/<pagina>.html` e rode o build. O cabeçalho, o menu e o rodapé são compartilhados entre as páginas e ficam em `tools/build.py` (`head()` e `FOOT`).
- **Desktop:** o HTML é gerado a partir do snapshot do Canva, então não edite `site/*.html` à mão. Para pequenas mudanças de texto, edite o texto em `extracao/snap/<pagina>.json` e rode o build. Para mudanças maiores, faça no Canva e capture de novo com `python tools/extract/snapshot.py` (precisa de `pip install playwright` e `playwright install chromium`), depois rode o build.
- **No celular, as imagens do desktop não são baixadas:** elas usam `data-src` e o `main.js` só as carrega quando o layout desktop está ativo.

## Páginas

| Página   | Arquivo         |
|----------|-----------------|
| Home     | `index.html`    |
| Sobre mim| `sobre.html`    |
| Projetos | `projetos.html` |
| Afude    | `afude.html`    |
| Eclipsa  | `eclipsa.html`  |
| Clo 3D   | `clo3d.html`    |
