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
window.fetch = () => Promise.reject(new Error('no network in test'));
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
check('compteur atelier', $('#lab-function-count').textContent.includes('15'), $('#lab-function-count').textContent);
check('date du jour', /SEPTEMBRE 2026/.test($('#dashboard-date').textContent), $('#dashboard-date').textContent.slice(0, 40));
check('notes vides au départ', $$('#saved-notes .saved-note').length >= 1);

// Navigation vers l'atelier DAX
$('.nav-item[data-route="lab"]').click();
check('vue atelier active', $('#view-lab').classList.contains('active-view'));
check('liste formules', $$('#formula-list .formula-item').length === 15, String($$('#formula-list .formula-item').length));
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

// Ouverture module 2 puis validation
$$('#dashboard-module-grid .module-card')[1].click();
check('vue leçon active', $('#view-lesson').classList.contains('active-view'));
check('titre module 2', $('#lesson-title').textContent.includes('Power BI Desktop'), $('#lesson-title').textContent);
check('sections leçon', $$('#lesson-article h2').length >= 8, String($$('#lesson-article h2').length));

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
$('#complete-lesson').click();
check('toast de validation', $('#toast').textContent.includes('Module validé'), $('#toast').textContent);
check('progression mise à jour', $('#sidebar-progress-value').textContent !== '12%', $('#sidebar-progress-value').textContent);

// Module verrouillé
const locked = $$('#path-list .path-row .path-body[aria-disabled="true"]');
check('modules verrouillés présents', locked.length >= 9, String(locked.length));

// Recherche
const si = $('#search-input');
si.value = 'DAX';
si.dispatchEvent(new window.Event('input', { bubbles: true }));
const found = $$('#dashboard-module-grid .module-card').length;
check('recherche DAX', found >= 2 && found < 12, String(found));
si.value = '';
si.dispatchEvent(new window.Event('input', { bubbles: true }));
check('recherche réinitialisée', $$('#dashboard-module-grid .module-card').length === 12);

// Notes
$('.nav-item[data-route="notes"]').click();
$('#note-text').value = 'CALCULATE modifie le contexte.';
$('#save-note').click();
check('note enregistrée', $$('#saved-notes .saved-note').length >= 1 && $('#saved-notes').textContent.includes('CALCULATE'));

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

console.log(results.join('\n'));
const fails = results.filter(r => r.startsWith('FAIL'));
if (warnings.length) console.log('\nAvertissements jsdom (attendus) : ' + warnings.length);
if (errors.length) console.log('\nERREURS CONSOLE:\n' + errors.join('\n'));
console.log(`\n${results.length - fails.length}/${results.length} contrôles OK`);
process.exit(fails.length || errors.length ? 1 : 0);
