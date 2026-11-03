# Portfólio Nathalia Dutra

Site de moda e design da Nathalia, migrado do Canva para HTML, CSS e JS puros.

- **Desktop (acima de 900px):** igual ao layout do Canva, escalado para a largura da janela.
- **Mobile (até 900px):** layout redesenhado, com a mesma identidade (janelas retrô, pixel font).

No ar: https://nathalia-dutra-nine.vercel.app

## Estrutura

```
src/
  mobile/<pagina>.html   ← markup do mobile (editar aqui)
  desktop/<pagina>.json  ← layout do desktop capturado do Canva
  css/style.css          ← estilos (fontes, mobile)
  js/main.js             ← zoom do desktop, carregamento de mídia, menu
  assets/                ← imagens, vídeos e fontes do site
  vercel.json            ← cache e URLs limpas
tools/build.py           ← gera site/ a partir de src/
site/                    ← site pronto (é o que vai para a Vercel)
```

## Gerar e testar

Precisa de Python 3 com Pillow (`pip install pillow`).

```bash
python tools/build.py
```

```bash
python -m http.server 8770 --directory site
```

Depois abra http://127.0.0.1:8770.

## Publicar (Vercel)

```bash
cd site && npx vercel@latest deploy --prod
```

A pasta `site/.vercel` guarda o vínculo com o projeto `nathalia-dutra`, então não apague `site/` inteira.

## Editar

- **Mobile:** edite `src/mobile/<pagina>.html` e rode o build. Cabeçalho, menu e rodapé ficam em `tools/build.py` (`head()` e `FOOT`).
- **Desktop:** gerado a partir de `src/desktop/*.json`; não edite `site/*.html` à mão. Pequenas mudanças de texto dá para fazer no JSON.
- **No celular, as imagens do desktop não são baixadas** (`data-src` + `main.js`).

Os scripts de extração do Canva, exportação para o Figma e o kit de assets foram removidos na limpeza, mas continuam no histórico do Git (commit anterior à limpeza).

## Páginas

| Página    | Arquivo         |
|-----------|-----------------|
| Home      | `index.html`    |
| Sobre mim | `sobre.html`    |
| Projetos  | `projetos.html` |
| Afude     | `afude.html`    |
| Eclipsa   | `eclipsa.html`  |
| Clo 3D    | `clo3d.html`    |
