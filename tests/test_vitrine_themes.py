"""Thèmes des boutiques (vitrine/themes.py) : chaque thème rend ses pages, avec ses propres textes.

Le thème est choisi à l'import de vitrine.app (VITRINE_PROJECT) : un processus par thème.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vitrine.themes import BASE, THEMES, theme_for  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

RENDER = r'''
import os, sys, json
sys.path.insert(0, os.getcwd())
import vitrine.app as va
products = [{"id": i, "name": f"Produit {i}", "category_id": 1, "price": 20.0, "price_from": 20.0, "compare_price": None,
             "is_new": False, "image_url": "https://x/i.jpg", "stock": 5} for i in (1, 2, 3)]
cat = {"products": products, "categories": [{"id": 1, "name": "Tout", "count": 3}], "free_shipping": {"threshold": 39}}
def fake(method, path, **kw):
    if path.startswith("/catalogue"): return cat
    if path.startswith("/storefront"): return {"lots": [{"name": "Lot test", "text": "t", "ids": [1, 2]}]}
    if path.startswith("/products/"):
        p = products[int(path.split("/")[-1]) - 1]
        return {**p, "images": [], "variants": [], "reviews": None, "description": "", "short_description": ""}
    raise va.ApiError("x")
va.api = fake
cl = va.app.test_client()
out = {}
for url in ("/", "/produit/1", f"/{va.THEME['lot_slug']}/0", "/rituel/0", "/panier"):
    r = cl.get(url)
    out[url] = [r.status_code, r.get_data(as_text=True)]
print(json.dumps(out))
'''


def render(project):
    env = {**os.environ, 'VITRINE_TESTING': '1', 'VITRINE_PROJECT': project, 'MPS_API': 'http://x'}
    run = subprocess.run([sys.executable, '-c', RENDER], cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
    assert run.returncode == 0, run.stderr[-3000:]
    import json
    return json.loads(run.stdout.strip().splitlines()[-1])


def test_every_theme_is_complete():
    for code in THEMES:
        theme = theme_for(code)
        assert set(theme) == set(BASE), code
        assert set(theme['palette']) == set(BASE['palette']), code
        assert theme['lot_slug'].isascii() and theme['lot_slug'].isalpha(), code


def test_unknown_project_falls_back_to_base():
    assert theme_for('inconnu')['hero_title'] == BASE['hero_title']


@pytest.mark.parametrize('code', sorted(THEMES))
def test_theme_pages_render(code):
    theme = theme_for(code)
    pages = render(code)
    for url, (status, _) in pages.items():
        assert status == 200, (code, url, status)
    home = pages['/'][1]
    assert theme['name'] in home and theme['nav_lots'] in home and 'Lot test' in home
    assert f"/{theme['lot_slug']}/0" in home
    assert theme['palette']['night'] in home
    # aucun texte propre à une autre boutique
    for other, t in THEMES.items():
        if other != code and t.get('hero_title'):
            assert t['hero_title'].replace("'", '&#39;') not in home, (code, other)
    if code != 'serenis':
        assert 'rituel' not in home.lower(), code
