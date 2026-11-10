"""Descarga capas del servicio ArcGIS público del IMIP (sigimip.org.mx) a data/raw/.

Las respuestas se guardan tal como las entrega el servidor (Esri JSON, una página
por archivo) para no alterar el original. Se registra un manifiesto con URL,
fecha de descarga y hash SHA-256 de cada página.

Uso:  python -m src.ingesta.arcgis_imip
"""
from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "https://sigimip.org.mx/server/rest/services"
RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "imip_arcgis"

# (servicio, id de capa) -> nombre de carpeta destino
LAYERS = {
    ("incidentesviales", 16): "incidentes_2023T",
    ("incidentesviales", 18): "incidentes_2024T",
    ("incidentesviales", 20): "incidentes_2025T",
    ("incidentesviales", 19): "cruceros_2025",
    ("incidentesviales", 41): "cruceros_mayor_incidencia",
    ("limitesyareasV2", 15): "limite_municipal",
    ("limitesyareasV2", 14): "centro_de_poblacion",
}


def _get_json(url: str, params: dict) -> tuple[bytes, dict]:
    full = f"{url}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(full, timeout=120) as resp:
        body = resp.read()
    data = json.loads(body)
    if "error" in data:
        raise RuntimeError(f"Error del servidor ArcGIS en {full}: {data['error']}")
    return body, data


def download_layer(service: str, layer_id: int, folder: str) -> dict:
    """Descarga todas las páginas de una capa y devuelve su entrada de manifiesto."""
    layer_url = f"{BASE_URL}/{service}/FeatureServer/{layer_id}"
    out = RAW_DIR / folder
    out.mkdir(parents=True, exist_ok=True)

    meta_body, meta = _get_json(layer_url, {"f": "json"})
    (out / "layer_metadata.json").write_bytes(meta_body)
    page_size = meta.get("maxRecordCount", 1000)
    _, cnt = _get_json(f"{layer_url}/query", {"where": "1=1", "returnCountOnly": "true", "f": "json"})
    total = cnt["count"]

    pages, offset, received = [], 0, 0
    while offset < total:
        params = {
            "where": "1=1", "outFields": "*", "returnGeometry": "true",
            "orderByFields": meta.get("objectIdField", "OBJECTID"),
            "resultOffset": offset, "resultRecordCount": page_size, "f": "json",
        }
        body, data = _get_json(f"{layer_url}/query", params)
        name = f"page_{offset:06d}.json"
        (out / name).write_bytes(body)
        n = len(data.get("features", []))
        received += n
        pages.append({"archivo": name, "registros": n, "sha256": hashlib.sha256(body).hexdigest()})
        if n == 0:
            break
        offset += n

    if received != total:
        raise RuntimeError(f"Capa {layer_id}: se esperaban {total} registros y llegaron {received}")
    return {
        "capa_id": layer_id, "nombre": meta.get("name"), "url": layer_url,
        "registros": total, "paginas": pages,
        "descargado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    for (service, layer_id), folder in LAYERS.items():
        entry = download_layer(service, layer_id, folder)
        print(f"Capa {layer_id} ({entry['nombre']}): {entry['registros']} registros")
        manifest.append(entry)
    (RAW_DIR / "manifiesto.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
