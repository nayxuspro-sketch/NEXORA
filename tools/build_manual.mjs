// Construit manuel.html à partir de FORMATION_POWER_BI.md
// Usage : node tools/build_manual.mjs
import { readFileSync, writeFileSync } from 'node:fs';
import { marked } from 'marked';

const md = readFileSync(new URL('../FORMATION_POWER_BI.md', import.meta.url), 'utf8');
const body = marked.parse(md, { gfm: true });

// Ancres sur les h1 (chapitres) + TOC
const toc = [];
let n = 0;
const withIds = body.replace(/<h1>([\s\S]*?)<\/h1>/g, (m, txt) => {
  const plain = txt.replace(/<[^>]+>/g, '').trim();
  if (n === 0) { n++; return m; } // titre principal ignoré
  const id = 'chapitre-' + n++;
  toc.push({ id, plain });
  return `<h1 id="${id}">${txt}</h1>`;
});

const tocHtml = toc.map(t => `<a class="manual-toc-link" href="#${t.id}">${t.plain}</a>`).join('');

const page = `<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex">
  <title>Manuel — Formation Power BI NEXORA</title>
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='22' fill='%23111b38'/%3E%3Crect x='24' y='54' width='14' height='24' rx='3' fill='%23f46b4f'/%3E%3Crect x='44' y='40' width='14' height='38' rx='3' fill='%23f7c95f'/%3E%3Crect x='64' y='26' width='14' height='52' rx='3' fill='%2352bc94'/%3E%3C/svg%3E">
  <link rel="stylesheet" href="styles.css">
</head>
<body class="manual-body">
  <header class="manual-topbar">
    <a class="manual-brand" href="index.html">✦ <strong>NEXORA</strong> · MANUEL</a>
    <div class="manual-actions"><a href="index.html">Retour à l’academy</a><button id="manual-print">Imprimer</button></div>
  </header>
  <div class="manual-layout">
    <aside class="manual-toc"><p class="eyebrow">SOMMAIRE</p>${tocHtml}</aside>
    <article class="manual-article">
${withIds}
      <footer class="manual-footer">Source : <a href="FORMATION_POWER_BI.md">FORMATION_POWER_BI.md</a> · Régénéré avec <code>node tools/build_manual.mjs</code></footer>
    </article>
  </div>
  <script>document.getElementById('manual-print').addEventListener('click',()=>window.print());</script>
</body>
</html>
`;
writeFileSync(new URL('../manuel.html', import.meta.url), page);
console.log('manuel.html écrit —', toc.length, 'entrées de sommaire');
