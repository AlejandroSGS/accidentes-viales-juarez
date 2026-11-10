"""Prueba de humo: la app arranca y cada página se dibuja sin errores (usa la BASE DE PRUEBAS)."""
import pytest
from streamlit.testing.v1 import AppTest

from src.config import ROOT

pytestmark = pytest.mark.db

APP = str(ROOT / "src" / "app" / "app.py")
PAGINAS = ["inicio", "explorar", "ranking", "concentracion", "mapa", "kmeans", "no_disponible", "calidad", "acerca"]


@pytest.fixture
def app(engine_pruebas, monkeypatch):
    monkeypatch.setenv("ACCIDENTES_BD_PRUEBAS", "1")
    from src.app import comun
    comun.engine.clear()
    at = AppTest.from_file(APP, default_timeout=180).run()
    yield at
    comun.engine.clear()


def test_app_arranca(app):
    assert not app.exception
    assert app.title[0].value == "Accidentes viales en Ciudad Juárez"
    assert [m.value for m in app.metric][:2] == ["6,423", "2,787"]
    assert any("No determinan las causas" in i.value for i in app.info)


@pytest.mark.parametrize("pagina", PAGINAS)
def test_cada_pagina_sin_errores(app, pagina):
    app.switch_page(f"paginas/{pagina}.py").run()
    assert not app.exception, [e.value for e in app.exception]
    assert app.title


def test_filtros_compartidos(app):
    app.multiselect(key="f_zonas").set_value(["ORIENTE"]).run()
    app.slider(key="f_min").set_value(3).run()
    assert [m.value for m in app.metric][:2] == ["630", "79"]
    app.switch_page("paginas/ranking.py").run()
    assert not app.exception
    assert "ORIENTE" in app.caption[0].value
