// Contrôle d'affichage des deux sites (MultiProShop et vitrine Sérénis) de 360 à 1920 px :
// footer en bas de page, texte de carte posé sur une image, défilement horizontal.
// Usage : node scripts/check_site_layout.js [dossier_captures]
//   MPS=https://multiproshop.com SER=https://serenis.multiproshop.com (valeurs par défaut)
//   WIDTHS=360,768 pour limiter les largeurs.
// Complète scripts/check_vitrine_layout.js, qui ne regarde que la vitrine.
const { chromium } = require('playwright');
const fs = require('fs');
const MPS = process.env.MPS || 'https://multiproshop.com';
const SER = process.env.SER || 'https://serenis.multiproshop.com';
const PAGES = [
  [MPS, '/'], [MPS, '/products/'], [MPS, '/products/category/1'], [MPS, '/products/880'], [MPS, '/cart/'],
  [MPS, '/about'], [MPS, '/contact'], [MPS, '/faq'], [MPS, '/legal'], [MPS, '/privacy'],
  [MPS, '/auth/connexion'], [MPS, '/auth/inscription'], [MPS, '/page-inexistante-404'], [MPS, '/search?q=zzzzqqq'],
  [SER, '/'], [SER, '/panier'], [SER, '/produit/20910'], [SER, '/rituel/0'], [SER, '/inexistant-404'],
];
const WIDTHS = (process.env.WIDTHS || '360,390,768,1024,1280,1920').split(',').map(Number);
const shots = process.argv[2];
if (shots) fs.mkdirSync(shots, { recursive: true });

(async () => {
  const b = await chromium.launch();
  const problems = [];
  for (const w of WIDTHS) {
    const ctx = await b.newContext({ viewport: { width: w, height: w < 768 ? 740 : 900 } });
    const p = await ctx.newPage();
    for (const [base, path] of PAGES) {
      await p.goto(base + path, { waitUntil: 'networkidle', timeout: 45000 }).catch(() => {});
      await p.evaluate(() => document.querySelectorAll('img[loading=lazy]').forEach(i => { i.loading = 'eager'; }));
      await p.waitForTimeout(800);
      const r = await p.evaluate(() => {
        const out = { footerGap: null, hOverflow: 0, overlaps: [] };
        const f = document.querySelector('footer');
        if (f) {
          // espace réservé sous le footer pour une barre fixe (bouton « Ajouter » mobile de la vitrine) : normal
          const reserved = parseFloat(getComputedStyle(document.body).paddingBottom) || 0;
          const bottom = f.getBoundingClientRect().bottom + scrollY;
          out.footerGap = Math.round(Math.max(innerHeight, document.documentElement.scrollHeight) - bottom - reserved);
        }
        out.hOverflow = document.documentElement.scrollWidth - innerWidth;
        for (const img of document.querySelectorAll('img')) {
          const ir = img.getBoundingClientRect();
          if (ir.width < 60 || ir.height < 60) continue;
          const card = img.closest('article, .card, .product-card, [class*="card"], li, a');
          if (!card) continue;
          // zone réellement visible de l'image (ses cadres peuvent la rogner)
          let box = { left: ir.left, right: ir.right, top: ir.top, bottom: ir.bottom };
          for (let el = img.parentElement; el && el !== card.parentElement; el = el.parentElement) {
            if (getComputedStyle(el).overflow === 'visible') continue;
            const er = el.getBoundingClientRect();
            box = { left: Math.max(box.left, er.left), right: Math.min(box.right, er.right), top: Math.max(box.top, er.top), bottom: Math.min(box.bottom, er.bottom) };
          }
          const walker = document.createTreeWalker(card, NodeFilter.SHOW_TEXT);
          for (let n; (n = walker.nextNode());) {
            const pe = n.parentElement;
            if (!n.textContent.trim() || !pe || pe.closest('button')) continue;
            const cs = getComputedStyle(pe);
            if (cs.visibility === 'hidden' || cs.display === 'none' || +cs.opacity === 0) continue;
            // badges volontairement posés sur l'image (position absolue) : ignorés
            let abs = false;
            for (let e = pe; e && e !== card; e = e.parentElement) if (['absolute', 'fixed'].includes(getComputedStyle(e).position)) { abs = true; break; }
            if (abs) continue;
            const range = document.createRange(); range.selectNodeContents(n);
            for (const tr of range.getClientRects()) {
              const ox = Math.min(tr.right, box.right) - Math.max(tr.left, box.left);
              const oy = Math.min(tr.bottom, box.bottom) - Math.max(tr.top, box.top);
              if (ox > 4 && oy > 4) { out.overlaps.push(n.textContent.trim().slice(0, 40)); break; }
            }
          }
        }
        out.overlaps = [...new Set(out.overlaps)].slice(0, 6);
        return out;
      });
      const issues = [];
      if (r.footerGap === null) issues.push('pas de <footer>');
      else if (r.footerGap > 2) issues.push(`footer pas en bas (vide ${r.footerGap}px)`);
      if (r.hOverflow > 1) issues.push(`débordement horizontal ${r.hOverflow}px`);
      if (r.overlaps.length) issues.push('texte sur image : ' + r.overlaps.join(' | '));
      if (issues.length) problems.push(`${w}px ${base}${path} -> ${issues.join(' ; ')}`);
      if (shots) await p.screenshot({ path: `${shots}/${w}_${base === SER ? 'ser' : 'mps'}${path.replace(/[^a-z0-9]+/gi, '_')}.png`, fullPage: true });
    }
    await ctx.close();
  }
  await b.close();
  console.log(problems.length ? problems.join('\n') : 'Tout est OK');
  process.exit(problems.length ? 1 : 0);
})();
