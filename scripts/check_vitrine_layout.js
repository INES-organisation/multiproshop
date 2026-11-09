// Contrôle d'affichage de la vitrine (débordements, footer en bas, texte sur image) à 320-1920 px.
// Usage : vitrine lancée sur BASE (défaut http://127.0.0.1:5099), puis node scripts/check_vitrine_layout.js [dossier_captures]
const { chromium } = require('playwright');
const base = process.env.BASE || 'http://127.0.0.1:5099';
const pages = ['/', '/?category=1', '/?prix=15', '/produit/20987', '/produit/21143', '/rituel/0', '/panier', '/commande', '/merci', '/produit/999999', '/rituel/9'];
const widths = [320, 360, 390, 768, 1024, 1366, 1920];
const shots = process.argv[2];
(async () => {
  const b = await chromium.launch(); let bad = 0;
  for (const w of widths) {
    const ctx = await b.newContext({ viewport: { width: w, height: w < 800 ? 740 : 900 } });
    const p = await ctx.newPage();
    for (const path of pages) {
      await p.goto(base + path); await p.waitForTimeout(150);
      const r = await p.evaluate(() => {
        const issues = [], de = document.documentElement;
        if (de.scrollWidth > innerWidth + 1) issues.push(`débordement horizontal ${de.scrollWidth}>${innerWidth}`);
        const fe = document.querySelector('footer.site'); if (!fe) return ['pas de footer'];const f = fe.getBoundingClientRect();
        if (f.bottom + scrollY < innerHeight - 1) issues.push(`footer pas en bas (${Math.round(f.bottom)} < ${innerHeight})`);
        const inter = (a, c) => Math.min(a.bottom, c.bottom) - Math.max(a.top, c.top) > 1 && Math.min(a.right, c.right) - Math.max(a.left, c.left) > 1;
        document.querySelectorAll('.card').forEach(c => {
          const im = c.querySelector('img').getBoundingClientRect(), box = c.querySelector('.img').getBoundingClientRect();
          c.querySelectorAll('.body *').forEach(t => { if (inter(t.getBoundingClientRect(), im)) issues.push('texte sur image: ' + c.querySelector('.name').textContent.slice(0, 30)); });
          if (im.height > box.height + 1) issues.push('image déborde de son cadre');
        });
        document.querySelectorAll('.ritual').forEach(c => {
          const col = c.querySelector('.collage').getBoundingClientRect();
          c.querySelectorAll('.collage img').forEach(i => { const ir = i.getBoundingClientRect(); if (ir.bottom > col.bottom + 1) issues.push('collage déborde'); });
          const h = c.querySelector('h3').getBoundingClientRect(); if (h.top < col.bottom) issues.push('titre rituel sur collage');
        });
        document.querySelectorAll('.gallery .main').forEach(m => { const i = m.querySelector('img').getBoundingClientRect(), r = m.getBoundingClientRect(); if (i.height > r.height + 1) issues.push('photo produit déborde'); });
        // tout élément visible qui dépasse à droite
        document.querySelectorAll('body *').forEach(e => { const r = e.getBoundingClientRect(); if (r.width && r.right > innerWidth + 1 && getComputedStyle(e).position !== 'fixed' && !e.closest('.thumbs,.chips,.stars')) issues.push('dépasse à droite: ' + e.tagName + '.' + e.className); });
        return [...new Set(issues)];
      });
      if (r.length) { bad++; console.log(w, path, r.slice(0, 6).join(' | ')); }
      if (shots && (w === 360 || w === 1366) && ['/', '/panier', '/produit/21143', '/rituel/0', '/merci'].includes(path))
        await p.screenshot({ path: `${shots}/${w}_${path.replace(/[\/?=]/g, '_') || 'accueil'}.png`, fullPage: true });
    }
    await ctx.close();
  }
  console.log(bad ? `${bad} page(s) avec problème` : 'Tout est OK');
  await b.close();
})();
