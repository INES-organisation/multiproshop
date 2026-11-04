"""« Se connecter avec INES » : aller-retour complet côté MultiProShop (INES simulé)."""
from unittest.mock import MagicMock
from urllib.parse import parse_qs, urlsplit

import pytest

from models.user import User
from services import ines_sso


def _resp(data):
    r = MagicMock()
    r.json.return_value = data
    r.raise_for_status.return_value = None
    return r


@pytest.fixture
def ines(monkeypatch):
    monkeypatch.setenv("INES_OIDC_CLIENT_ID", "multiproshop")
    monkeypatch.setenv("INES_OIDC_CLIENT_SECRET", "secret")
    profile = {"sub": "ines-1", "email": "Admin@Test.com", "email_verified": True, "preferred_username": "admin"}
    monkeypatch.setattr(ines_sso.requests, "post", lambda *a, **kw: _resp({"access_token": "at"}))
    monkeypatch.setattr(ines_sso.requests, "get", lambda *a, **kw: _resp(profile))
    return profile


def _login(client):
    r = client.get("/auth/ines")
    state = parse_qs(urlsplit(r.headers["Location"]).query)["state"][0]
    return client.get("/auth/ines/callback", query_string={"code": "c", "state": state})


def test_button_and_link_by_email(client, app, ines):
    assert b"/auth/ines" in client.get("/auth/connexion").data
    with app.app_context():
        before = User.query.count()
    r = _login(client)
    assert r.status_code == 302 and "/auth/connexion" not in r.headers["Location"]
    with app.app_context():
        assert User.query.count() == before  # compte existant lié, pas de doublon
        assert User.query.filter_by(ines_sub="ines-1").one().email == "admin@test.com"


def test_new_account_and_bad_state(client, app, ines):
    ines.update(sub="ines-2", email="nouveau@site.test", preferred_username="admin")
    assert "/auth/connexion" in client.get("/auth/ines/callback?code=c&state=faux").headers["Location"]
    _login(client)
    with app.app_context():
        u = User.query.filter_by(ines_sub="ines-2").one()
        assert u.email == "nouveau@site.test" and u.username != "admin"
