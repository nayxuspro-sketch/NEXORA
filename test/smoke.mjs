// Smoke test NEXORA — lance : node test/smoke.mjs
import { readFileSync } from 'node:fs';
import { JSDOM, VirtualConsole } from 'jsdom';

const errors = [];
const warnings = [];
const vc = new VirtualConsole();
vc.on('jsdomError', e => {
  // jsdom n'implémente pas scrollTo/navigate : à ignorer
  if (e.message.includes('Not implemented')) warnings.push(e.message);
  else errors.push('jsdomError: ' + e.message);
});
vc.on('error', (...a) => errors.push('console.error: ' + a.join(' ')));

const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const appJs = readFileSync(new URL('../app.js', import.meta.url), 'utf8');

const dom = new JSDOM(html, {
  url: 'http://localhost:4173/',
  runScripts: 'outside-only',
  pretendToBeVisual: true,
  virtualConsole: vc
});
const { window } = dom;
window.fetch = () => Promise.resolve({ ok: true, text: () => Promise.resolve('ColonneA,ColonneB\n1,2\n'), arrayBuffer: () => Promise.resolve(new Uint8Array([0x50, 0x4B, 0x03, 0x04]).buffer) });
try {
  if (!window.URL.createObjectURL) window.URL.createObjectURL = () => 'blob:nexora';
  if (!window.URL.revokeObjectURL) window.URL.revokeObjectURL = () => {};
} catch (e) { /* noop */ }
try {
  window.eval(appJs);
} catch (e) {
  errors.push('app.js threw: ' + e.stack);
}

const $ = s => window.document.querySelector(s);
const $$ = s => [...window.document.querySelectorAll(s)];
const results = [];
const check = (name, cond, extra = '') => results.push(`${cond ? 'PASS' : 'FAIL'}  ${name}${extra ? ' — ' + extra : ''}`);

check('12 cartes modules dashboard', $$('#dashboard-module-grid .module-card').length === 12, String($$('#dashboard-module-grid .module-card').length));
check('12 lignes parcours', $$('#path-list .path-row').length === 12);
check('module 1 terminé', $$('#path-list .path-row.done').length === 1);
check('progression affichée', /\d+%/.test($('#sidebar-progress-value').textContent), $('#sidebar-progress-value').textContent);
check('lexique rendu', $$('#glossary-terms .glossary-term').length === 48, String($$('#glossary-terms .glossary-term').length));
check('compteur lexique', $('#glossary-count').textContent.includes('48'), $('#glossary-count').textContent);
check('compteur atelier', $('#lab-function-count').textContent.includes('18'), $('#lab-function-count').textContent);
check('date du jour', /SEPTEMBRE 2026/.test($('#dashboard-date').textContent), $('#dashboard-date').textContent.slice(0, 40));
check('notes vides au départ', $$('#saved-notes .saved-note').length >= 1);

// Propreté du DOM : aucun identifiant dupliqué
const idList = [...window.document.querySelectorAll('[id]')].map(e => e.id);
const dupIds = idList.filter((v, i) => idList.indexOf(v) !== i);
check('aucun id dupliqué (accueil)', dupIds.length === 0, dupIds.join(','));

// Navigation vers l'atelier DAX
$('.nav-item[data-route="lab"]').click();
check('vue atelier active', $('#view-lab').classList.contains('active-view'));
check('liste formules', $$('#formula-list .formula-item').length === 18, String($$('#formula-list .formula-item').length));
check('détail formule affiché', $('#formula-detail').textContent.includes('SUM'));

// Sélection d'une autre formule
$$('#formula-list .formula-item')[3].click();
check('formule CALCULATE sélectionnée', $('#formula-detail').textContent.includes('CALCULATE'));

// Défi express
$('[data-answer="right"]').click();
check('défi : bonne réponse', $('#challenge-feedback').textContent.startsWith('✓'));

// Ressources : lexique + définition
$('.nav-item[data-route="ressources"]').click();
$$('#glossary-terms .glossary-term')[0].click();
check('définition lexique', $('#glossary-definition').textContent.includes('Relancer les requêtes'), $('#glossary-definition').textContent.slice(0, 50));

// Checklist modale
$('#checklist-button').click();
check('modale ouverte', !$('#modal-overlay').hidden);
check('18 points checklist', $$('#modal-content .checklist-list li').length === 18, String($$('#modal-content .checklist-list li').length));
$('#modal-close').click();
check('modale fermée', $('#modal-overlay').hidden);

// Jeux de données d'exercice
check('5 fichiers d’exercice', $$('[data-download]').length === 5, String($$('[data-download]').length));
check('bouton contoso présent', !!$('#download-dataset'));
$('[data-download="data/notes_exercice.csv"]').click();
await new Promise(r => setTimeout(r, 60));
check('téléchargement multi-fichiers', /Fichier téléchargé : notes_exercice\.csv/.test($('#toast').textContent), $('#toast').textContent);
$('[data-download="data/contoso_exercice.xlsx"]').click();
await new Promise(r => setTimeout(r, 60));
check('téléchargement Excel (.xlsx)', /Fichier téléchargé : contoso_exercice\.xlsx/.test($('#toast').textContent), $('#toast').textContent);
const xlsBuf = readFileSync(new URL('../data/contoso_exercice.xlsx', import.meta.url));
check('xlsx valide (en-tête PK)', xlsBuf[0] === 0x50 && xlsBuf[1] === 0x4B, String(xlsBuf.slice(0, 2)));

// Ouverture module 2 puis validation
$$('#dashboard-module-grid .module-card')[1].click();
check('vue leçon active', $('#view-lesson').classList.contains('active-view'));
check('titre module 2', $('#lesson-title').textContent.includes('Power BI Desktop'), $('#lesson-title').textContent);
check('sections leçon', $$('#lesson-article h2').length >= 8, String($$('#lesson-article h2').length));

// Pagination précédent / suivant en fin de leçon
check('pagination présente', $$('#lesson-article .lesson-pagination .page-nav').length === 2, String($$('#lesson-article .lesson-pagination .page-nav').length));
check('suivant verrouillé avant validation', $('#lesson-article .page-nav.next').disabled === true);
$('#lesson-article .page-nav.prev').click();
check('pagination → module 1', $('#view-lesson').classList.contains('active-view') && $('#lesson-title').textContent.includes('Business Intelligence'), $('#lesson-title').textContent);
$$('#path-list .path-row')[1].click();
check('retour au module 2', $('#lesson-title').textContent.includes('Desktop'), $('#lesson-title').textContent);

// Quiz du module (3 questions)
check('quiz : 3 questions', $$('#lesson-article .quiz-question').length === 3, String($$('#lesson-article .quiz-question').length));
check('quiz : zone score', !!$('#lesson-article .quiz-score'));
// Q1 réponse correcte (index 1), Q2 fausse (index 1), Q3 correcte (index 1)
$('[data-quiz-mod="2"][data-quiz-q="0"][data-quiz-choice="1"]').click();
check('quiz : feedback correct', $('#lesson-article .quiz-feedback.ok')?.textContent.includes('✓ Exact'), $('#lesson-article .quiz-feedback')?.textContent.slice(0, 40));
$('[data-quiz-mod="2"][data-quiz-q="1"][data-quiz-choice="1"]').click();
check('quiz : feedback incorrect', !!$('#lesson-article .quiz-feedback.ko'));
$('[data-quiz-mod="2"][data-quiz-q="2"][data-quiz-choice="1"]').click();
check('quiz : score final 2/3', $('#lesson-article .quiz-score').textContent.includes('2/3'), $('#lesson-article .quiz-score').textContent.trim());
check('quiz : choix verrouillés', $$('#lesson-article .quiz-option[disabled]').length === 9, String($$('#lesson-article .quiz-option[disabled]').length));

// Sommaire de leçon : les ancres ne doivent pas déclencher le routage
$('#lesson-toc-links .toc-link').click();
check('TOC reste sur la leçon', $('#view-lesson').classList.contains('active-view'));
check('TOC ne casse pas le hash', !window.location.hash.includes('section'), window.location.hash);
$('#complete-lesson').click();
check('toast de validation', $('#toast').textContent.includes('Module validé'), $('#toast').textContent);
check('progression mise à jour', $('#sidebar-progress-value').textContent !== '12%', $('#sidebar-progress-value').textContent);
check('suivant déverrouillé après validation', $('#lesson-article .page-nav.next').disabled === false);

// Module verrouillé
const locked = $$('#path-list .path-row .path-body[aria-disabled="true"]');
check('modules verrouillés présents', locked.length >= 9, String(locked.length));

// Recherche globale : dropdown groupé
const si = $('#search-input');
si.value = 'DAX';
si.dispatchEvent(new window.Event('input', { bubbles: true }));
check('dropdown recherche ouvert', !$('#search-results').hidden);
check('résultats : modules DAX', $$('#search-results [data-sr="module"]').length >= 2, String($$('#search-results [data-sr="module"]').length));
check('résultats : formules DAX', $$('#search-results [data-sr="formula"]').length >= 2, String($$('#search-results [data-sr="formula"]').length));
si.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
check('Entrée → parcours filtré', $('#view-parcours').classList.contains('active-view') && $$('#dashboard-module-grid .module-card').length === 2, String($$('#dashboard-module-grid .module-card').length));
si.value = '';
si.dispatchEvent(new window.Event('input', { bubbles: true }));
check('recherche réinitialisée', $$('#dashboard-module-grid .module-card').length === 12 && $('#search-results').hidden);
si.value = 'CALCUL';
si.dispatchEvent(new window.Event('input', { bubbles: true }));
const termBtn = $('#search-results [data-sr="term"]');
check('résultat lexique présent', !!termBtn);
termBtn.click();
check('lexique ouvert sur terme', $('#view-ressources').classList.contains('active-view') && $('#glossary-definition').textContent.includes('CALCULATE'), $('#glossary-definition').textContent.slice(0, 45));
si.value = 'SWITCH';
si.dispatchEvent(new window.Event('input', { bubbles: true }));
const fBtn = $('#search-results [data-sr="formula"]');
check('résultat formule présent', !!fBtn);
fBtn.click();
check('atelier ouvert sur la formule', $('#view-lab').classList.contains('active-view') && $('#formula-detail').textContent.includes('SWITCH'));
si.value = '';
si.dispatchEvent(new window.Event('input', { bubbles: true }));

// Notes
$('.nav-item[data-route="notes"]').click();
$('#note-text').value = 'CALCULATE modifie le contexte.';
$('#save-note').click();
check('note enregistrée', $$('#saved-notes .saved-note').length >= 1 && $('#saved-notes').textContent.includes('CALCULATE'));
check('bouton export notes', !!$('#export-notes'));
try { if (!window.URL.createObjectURL) window.URL.createObjectURL = () => 'blob:nexora'; if (!window.URL.revokeObjectURL) window.URL.revokeObjectURL = () => {}; } catch (e) { /* noop */ }
$('#export-notes').click();
check('export notes : toast', /exportée/.test($('#toast').textContent), $('#toast').textContent);
const manualHtml = readFileSync(new URL('../manuel.html', import.meta.url), 'utf8');
check('manuel : annexe lexique 48 termes', manualHtml.includes('Annexe C — Lexique illustré (48 termes)'));
check('manuel : sommaire enrichi', (manualHtml.match(/manual-toc-link/g) || []).length >= 15, String((manualHtml.match(/manual-toc-link/g) || []).length));

// Persistance
check('localStorage progression', JSON.parse(window.localStorage.getItem('nexora-completed')).includes(2));
check('localStorage notes', JSON.parse(window.localStorage.getItem('nexora-notes')).length >= 1);
check('localStorage quiz', JSON.parse(window.localStorage.getItem('nexora-quizzes'))['2'].length === 3);

// Export / import de progression
check('bouton export présent', !!$('#export-progress'));
check('bouton import présent', !!$('#import-progress'));
check('badge quiz sur carte module', $$('#dashboard-module-grid .module-card')[1].textContent.includes('Quiz 2/3'), $$('#dashboard-module-grid .module-card')[1].textContent.match(/Quiz \d\/\d/)?.[0] || 'absent');
const payload = JSON.stringify({ version: 1, completed: [1, 2, 3], current: 3, notes: [{ text: 'note import', date: '27 sept.' }], quizzes: { 2: [1, 1, 1] } });
const file = new window.File([payload], 'nexora_progression.json', { type: 'application/json' });
window.importProgress(file);
await new Promise(r => setTimeout(r, 100));
check('import : modules', JSON.parse(window.localStorage.getItem('nexora-completed')).join(',') === '1,2,3', window.localStorage.getItem('nexora-completed'));
check('import : module courant', window.localStorage.getItem('nexora-current') === '3');
check('import : notes remplacées', JSON.parse(window.localStorage.getItem('nexora-notes'))[0].text === 'note import');
check('import : progression visible', $('#sidebar-progress-value').textContent === '25%', $('#sidebar-progress-value').textContent);

// Profil, activité réelle et certificat
check('prénom par défaut', $('#greeting-name').textContent === 'Alex', $('#greeting-name').textContent);
try { window.prompt = () => 'Marie Dupont'; } catch (e) { Object.defineProperty(window, 'prompt', { value: () => 'Marie Dupont' }); }
$('#rename-profile').click();
check('renomage appliqué', $('#greeting-name').textContent === 'Marie' && $('#profile-name').textContent === 'Marie Dupont', $('#greeting-name').textContent + ' / ' + $('#profile-name').textContent);
check('initiales mises à jour', $('#profile-initials').textContent === 'MD', $('#profile-initials').textContent);
check('nom persisté', window.localStorage.getItem('nexora-name') === 'Marie Dupont');
check('barres activité : 7 jours', $$('#activity-bars > div').length === 7, String($$('#activity-bars > div').length));
const todayBar = $$('#activity-bars > div').pop();
check('activité du jour tracée', !todayBar.classList.contains('empty') && todayBar.querySelector('span').style.height !== '6%', todayBar.querySelector('span').style.height);
check('total activité honnête', /action/.test($('#activity-total').textContent), $('#activity-total').textContent.trim());
check('certificat masqué à 12/12', $('#certificate-banner').hidden === true);
const fullPayload = JSON.stringify({ version: 1, completed: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], current: 12, notes: [], quizzes: { 2: [1, 1, 1] } });
window.importProgress(new window.File([fullPayload], 'nexora_progression.json', { type: 'application/json' }));
await new Promise(r => setTimeout(r, 100));
check('certificat visible à 12/12', $('#certificate-banner').hidden === false);
check('progression 100 %', $('#sidebar-progress-value').textContent === '100%', $('#sidebar-progress-value').textContent);
$('#open-certificate').click();
check('modale certificat ouverte', !$('#modal-overlay').hidden && $('#modal-content').textContent.includes('Marie Dupont'));
check('certificat : bouton imprimer', !!$('#print-certificate'));
$('#print-certificate').click();
$('#modal-close').click();
check('modale certificat fermée', $('#modal-overlay').hidden);

// Routage par URL : bouton retour, favoris et liens profonds
$('.nav-item[data-route="dashboard"]').click();
check('hash → dashboard', window.location.hash === '#dashboard' && $('#view-dashboard').classList.contains('active-view'), window.location.hash);
$('.nav-item[data-route="lab"]').click();
check('hash → lab', window.location.hash === '#lab' && $('#view-lab').classList.contains('active-view'), window.location.hash);
check('aria-current sur la vue active', $('.nav-item[data-route="lab"]').getAttribute('aria-current') === 'page' && !$('.nav-item[data-route="dashboard"]').hasAttribute('aria-current'));
check('aria-expanded initial du menu', $('#mobile-menu').getAttribute('aria-expanded') === 'false');
$('#mobile-menu').click();
check('menu mobile ouvert (aria)', $('#mobile-menu').getAttribute('aria-expanded') === 'true' && $('#sidebar').classList.contains('open'));
$('#mobile-menu').click();
check('menu mobile fermé (aria)', $('#mobile-menu').getAttribute('aria-expanded') === 'false' && !$('#sidebar').classList.contains('open'));
window.location.hash = '#dashboard';
await new Promise(r => setTimeout(r, 30));
check('bouton retour navigateur', $('#view-dashboard').classList.contains('active-view'));
window.location.hash = '#module/1';
await new Promise(r => setTimeout(r, 30));
check('lien profond module', $('#view-lesson').classList.contains('active-view') && $('#lesson-title').textContent.includes('Business Intelligence'), $('#lesson-title').textContent);
window.location.hash = '#module/99';
await new Promise(r => setTimeout(r, 30));
check('route invalide → dashboard', $('#view-dashboard').classList.contains('active-view'));

// Page manuel et balises de tête
check('lien manuel HTML', $('.resource-card a[href="manuel.html"]') !== null);
check('favicon en tête', $('link[rel="icon"]') !== null);
check('meta description', ($('meta[name="description"]')?.content || '').includes('Power BI'));

// Recommencer le quiz (à la fin : efface le score du module 2)
$$('#dashboard-module-grid .module-card')[1].click();
check('réouverture module 2', $('#view-lesson').classList.contains('active-view') && $('#lesson-title').textContent.includes('Desktop'));
check('bouton recommencer visible', !!$('#reset-quiz'));
$('#reset-quiz').click();
check('quiz réinitialisé', !$('#reset-quiz') && $('#lesson-article .quiz-score').textContent.includes('0/3'), $('#lesson-article .quiz-score').textContent.trim());
check('options de nouveau actives', $$('#lesson-article .quiz-option:not([disabled])').length === 9, String($$('#lesson-article .quiz-option:not([disabled])').length));

// Propreté du DOM après rendu d'une leçon complète
const lessonIds = [...window.document.querySelectorAll('[id]')].map(e => e.id);
const dupLesson = lessonIds.filter((v, i) => lessonIds.indexOf(v) !== i);
check('aucun id dupliqué (leçon)', dupLesson.length === 0, dupLesson.join(','));

// Résilience : démarre même avec un localStorage corrompu
{
  const errs2 = [];
  const vc2 = new VirtualConsole();
  vc2.on('jsdomError', e => { if (!e.message.includes('Not implemented')) errs2.push(e.message); });
  const dom2 = new JSDOM(readFileSync(new URL('../index.html', import.meta.url), 'utf8'), { url: 'http://localhost:4173/', runScripts: 'outside-only', pretendToBeVisual: true, virtualConsole: vc2 });
  const w2 = dom2.window;
  w2.localStorage.setItem('nexora-completed', '{broken json');
  w2.localStorage.setItem('nexora-current', 'NaN');
  w2.localStorage.setItem('nexora-notes', '"pas un tableau"');
  w2.localStorage.setItem('nexora-quizzes', 'xyz');
  w2.fetch = () => Promise.resolve({ ok: true, text: () => Promise.resolve('a,b\n1,2') });
  let threw = null;
  try { w2.eval(readFileSync(new URL('../app.js', import.meta.url), 'utf8')); } catch (e) { threw = e.message; }
  check('démarrage avec stockage corrompu', threw === null && errs2.length === 0, threw || errs2.join(' | '));
  check('modules restaurés par défaut', w2.document.querySelectorAll('#dashboard-module-grid .module-card').length === 12, String(w2.document.querySelectorAll('#dashboard-module-grid .module-card').length));
  check('progression par défaut saine', w2.document.querySelector('#sidebar-progress-value').textContent === '12%', w2.document.querySelector('#sidebar-progress-value').textContent);
  w2.document.querySelector('#note-text').value = 'note de récupération';
  w2.document.querySelector('#save-note').click();
  check('note enregistrable malgré corruption', w2.document.querySelector('#saved-notes').textContent.includes('note de récupération'));
}

// Intégrité pédagogique du contenu (export de debug)
{
  const N = window.__nexora;
  check('export de debug présent', !!N && N.modules.length === 12 && N.quizzes);
  const problems = [];
  for (const m of N.modules) {
    if (!m.objectives || m.objectives.length < 3) problems.push(`M${m.id}:objectifs`);
    if (!m.demo || !Array.isArray(m.demo.steps) || m.demo.steps.length < 4 || !m.demo.result) problems.push(`M${m.id}:démo`);
    if (!m.formula || !m.formula.code || !m.formula.explanation) problems.push(`M${m.id}:formule`);
    for (const key of ['errors', 'best']) if (!Array.isArray(m[key]) || m[key].length < 3) problems.push(`M${m.id}:${key}`);
    for (const key of ['guided', 'autonomous', 'correction', 'project', 'prereq', 'subtitle', 'short']) if (!m[key] || String(m[key]).length < 20) problems.push(`M${m.id}:${key}`);
    if (!/^\d+\s*(min|h)(\s*\d+)?$/.test(m.time || '')) problems.push(`M${m.id}:time(${m.time})`);
    if (!m.content || (m.content.match(/<h2>/g) || []).length < 2) problems.push(`M${m.id}:contenu`);
    const o = (m.content.match(/«/g) || []).length, c = (m.content.match(/»/g) || []).length;
    if (o !== c) problems.push(`M${m.id}:guillemets ${o}/${c}`);
  }
  check('contenu complet des 12 modules', problems.length === 0, problems.join(','));
  const quizProblems = [];
  const ids = Object.keys(N.quizzes);
  for (const id of ids) {
    const qs = N.quizzes[id];
    if (qs.length !== 3) quizProblems.push(`M${id}:${qs.length}q`);
    qs.forEach((q, i) => { if (!q.q || !Array.isArray(q.o) || q.o.length !== 3 || !(Number.isInteger(q.a) && q.a >= 0 && q.a < 3) || !q.why) quizProblems.push(`M${id}.Q${i + 1}`); });
  }
  check('quiz : 3 questions valides × 12 modules', ids.length === 12 && quizProblems.length === 0, quizProblems.join(','));
  const badF = N.formulas.filter(f => !f.name || !f.code || !f.description || !f.result || !f.use || !f.error || !f.tag);
  check('18 fiches DAX complètes', N.formulas.length === 18 && badF.length === 0, badF.map(f => f.name || '?').join(','));
  check('lexique : 48 définitions substantielles', N.glossary.length === 48 && N.glossary.every(g => g.t && g.d && g.d.length > 30));
  const totalLessons = N.modules.reduce((a, m) => a + m.lessons, 0);
  check('48 leçons annoncées = somme des modules', totalLessons === 48, String(totalLessons));
  const mdText = readFileSync(new URL('../FORMATION_POWER_BI.md', import.meta.url), 'utf8');
  const mdO = (mdText.match(/«/g) || []).length, mdC = (mdText.match(/»/g) || []).length;
  check('guillemets équilibrés dans le manuel', mdO === mdC && mdO >= 10, `${mdO}/${mdC}`);
}

// Intégrité des fichiers, téléchargements et ancres
const { existsSync } = await import('node:fs');
const dlPaths = $$('[data-download]').map(b => b.dataset.download);
const missing = dlPaths.filter(pp => !existsSync(new URL('../' + pp, import.meta.url)));
check('fichiers de téléchargement présents sur disque', dlPaths.length === 5 && missing.length === 0, missing.join(','));
check('skip link et cible de contenu', !!$('.skip-link') && !!$('#main-content') && $('.skip-link').getAttribute('href') === '#main-content');
const anchorHrefs = [...manualHtml.matchAll(/href="#([^"]+)"/g)].map(m => m[1]);
const anchorIds = [...manualHtml.matchAll(/id="([^"]+)"/g)].map(m => m[1]);
const brokenAnchors = anchorHrefs.filter(a => !anchorIds.includes(a));
check('ancres du manuel valides', anchorHrefs.length >= 15 && brokenAnchors.length === 0, brokenAnchors.join(','));
check('assets principaux présents', ['styles.css', 'app.js', 'manuel.html', 'FORMATION_POWER_BI.md'].every(f => existsSync(new URL('../' + f, import.meta.url))));
check('annexe DAX du manuel à jour', manualHtml.includes('SAMEPERIODLASTYEAR') && manualHtml.includes('Marge % = DIVIDE'), 'DIVIDE + SAMEPERIODLASTYEAR');
const cssText = readFileSync(new URL('../styles.css', import.meta.url), 'utf8');
check('styles : prefers-reduced-motion', cssText.includes('prefers-reduced-motion'));

// Manuel PDF
check('lien PDF dans les ressources', !!$('.resource-card a[href="Formation_Power_BI_NEXORA.pdf"]'));
const pdfPath = new URL('../Formation_Power_BI_NEXORA.pdf', import.meta.url);
check('fichier PDF présent', existsSync(pdfPath));
const pdfBuf = readFileSync(pdfPath);
check('PDF valide (> 100 Ko, en-tête %PDF)', pdfBuf.slice(0, 5).toString() === '%PDF-' && pdfBuf.length > 100000, String(pdfBuf.length));
const pageMarks = pdfBuf.toString('latin1').match(/\/Type\s*\/Page[^s]/g) || [];
check('PDF : au moins 30 pages', pageMarks.length >= 30, String(pageMarks.length));

console.log(results.join('\n'));
const fails = results.filter(r => r.startsWith('FAIL'));
if (warnings.length) console.log('\nAvertissements jsdom (attendus) : ' + warnings.length);
if (errors.length) console.log('\nERREURS CONSOLE:\n' + errors.join('\n'));
console.log(`\n${results.length - fails.length}/${results.length} contrôles OK`);
process.exit(fails.length || errors.length ? 1 : 0);
