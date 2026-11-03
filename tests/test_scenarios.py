"""Scénarios de bout en bout (paiement, publication CJ, livraison, codes promo, newsletter…).

Chaque fichier de tests/scenarios/ est un script autonome : il monte l'application en mode testing
(SQLite en mémoire), simule CJ, Stripe et INES, et s'arrête sur la première assertion fausse.
Lancés un par un dans leur propre processus, car chacun réinitialise l'application.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCENARIOS = sorted((Path(__file__).parent / 'scenarios').glob('*.py'))


@pytest.mark.parametrize('script', SCENARIOS, ids=[s.stem[3:] for s in SCENARIOS])
def test_scenario(script):
    env = {**os.environ, 'FLASK_ENV': 'testing'}
    env.pop('INES_API_KEY', None)
    run = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=300, env=env)
    assert run.returncode == 0, (run.stdout[-2000:] + run.stderr[-4000:])
