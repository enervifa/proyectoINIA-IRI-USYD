import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SOURCE_DIR = DATA_DIR / "source"


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def to_bool(value, default=False):
    if value is None:
        return default
    s = str(value).strip().lower()
    if s in ("1", "true", "yes", "y", "si", "sí"):
        return True
    if s in ("0", "false", "no", "n"):
        return False
    return default


def to_int(value, default=None):
    if value is None:
        return default
    s = str(value).strip()
    if not s:
        return default
    try:
        return int(float(s))
    except Exception:
        return default


def to_float(value, default=None):
    if value is None:
        return default
    s = str(value).strip()
    if not s:
        return default
    try:
        return float(s)
    except Exception:
        return default


def split_list(value):
    if value is None:
        return []
    s = str(value).strip()
    if not s:
        return []
    # Accept ";" or "," from Excel exports.
    parts = []
    for chunk in s.replace("|", ";").replace(",", ";").split(";"):
        v = chunk.strip()
        if v:
            parts.append(v)
    return parts


def write_json(path: Path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def first_value(row: dict, *keys: str) -> str:
    for key in keys:
        if key in row and row.get(key) not in (None, ""):
            return row.get(key)
    return ""


def build_models(models_csv: Path):
    rows = read_csv(models_csv)
    models = []
    max_id = 0
    max_order = 0

    # First pass to track max values.
    for row in rows:
        max_id = max(max_id, to_int(first_value(row, "id"), 0))
        max_order = max(max_order, to_int(first_value(row, "table_order", "orden_tabla"), 0))

    next_id = max_id + 1
    next_order = max_order + 1

    for row in rows:
        model_id = to_int(first_value(row, "id"))
        if model_id is None:
            model_id = next_id
            next_id += 1

        table_order = to_int(first_value(row, "table_order", "orden_tabla"))
        if table_order is None:
            table_order = next_order
            next_order += 1

        name = (first_value(row, "name", "nombre") or "").strip()
        if not name:
            continue

        model = {
            "id": model_id,
            "name": name,
            "themes": (first_value(row, "themes", "temas") or "").strip(),
            "type": (first_value(row, "type", "tipo") or "").strip(),
            "scale": (first_value(row, "scale", "escala") or "").strip(),
            "status": (first_value(row, "status", "estado") or "").strip(),
            "description": (first_value(row, "description", "descripcion") or "").strip(),
            "website": (first_value(row, "website", "sitio_web") or "").strip(),
            "latitude": to_float(first_value(row, "latitude", "latitud")),
            "longitude": to_float(first_value(row, "longitude", "longitud")),
            "location": (first_value(row, "location", "ubicacion") or "").strip(),
            "keywords": split_list(first_value(row, "keywords", "palabras_clave")),
            "map_link": (first_value(row, "map_link", "enlace_mapa") or "").strip(),
            "table_order": table_order,
            "table_name": (first_value(row, "table_name", "nombre_tabla") or name).strip(),
            "table_scale": (
                first_value(row, "table_scale", "escala_tabla") or first_value(row, "scale", "escala") or ""
            ).strip(),
            "swat_model": (first_value(row, "swat_model", "modelo_swat") or "").strip(),
            "active_to_date": (first_value(row, "active_to_date", "activo_a_la_fecha") or "").strip(),
            "show_in_catalogue": to_bool(first_value(row, "show_in_catalogue", "mostrar_en_catalogo"), default=True),
        }

        # Drop empty optional scalars to keep JSON compact.
        for k in ("latitude", "longitude"):
            if model[k] is None:
                model.pop(k, None)

        models.append(model)

    return models


def build_resources(resources_csv: Path):
    rows = read_csv(resources_csv)
    out = {}
    for row in rows:
        model_id = to_int(row.get("model_id"))
        catchment = (row.get("catchment") or "").strip()
        if model_id is None and not catchment:
            continue

        key = model_id if model_id is not None else catchment
        out.setdefault(key, {"model_id": model_id, "catchment": catchment, "items": []})

        title = (row.get("title") or "").strip()
        if not title:
            continue

        item = {
            "type": (row.get("type") or "").strip(),
            "title": title,
            "url": (row.get("url") or "").strip(),
        }
        authors = (row.get("authors") or "").strip()
        year = to_int(row.get("year"))
        if authors:
            item["authors"] = authors
        if year is not None:
            item["year"] = year

        out[key]["items"].append(item)

    # Stable output order: numeric ids first, then catchment keys.
    entries = list(out.values())
    entries.sort(key=lambda e: (e["model_id"] is None, e["model_id"] or 0, e["catchment"] or ""))
    return entries


def build_keywords(keywords_csv: Path):
    rows = read_csv(keywords_csv)
    out = []
    for row in rows:
        model_id = to_int(row.get("model_id"))
        catchment = (row.get("catchment") or "").strip()
        keywords = split_list(row.get("keywords"))
        if model_id is None and not catchment:
            continue
        out.append({"model_id": model_id, "catchment": catchment, "keywords": keywords})

    out.sort(key=lambda e: (e["model_id"] is None, e["model_id"] or 0, e["catchment"] or ""))
    return out


def build_institutions(institutions_csv: Path):
    rows = read_csv(institutions_csv)
    out = []
    for row in rows:
        name = (row.get("name") or "").strip()
        url = (row.get("url") or "").strip()
        if not name:
            continue
        out.append({"name": name, "url": url})
    return out


def main():
    parser = argparse.ArgumentParser(description="Build GMIC site JSON from CSV exports.")
    parser.add_argument("--models", default=str(SOURCE_DIR / "models.csv"))
    parser.add_argument("--resources", default=str(SOURCE_DIR / "resources.csv"))
    parser.add_argument("--keywords", default=str(SOURCE_DIR / "keywords.csv"))
    parser.add_argument("--institutions", default=str(SOURCE_DIR / "institutions.csv"))
    args = parser.parse_args()

    models_csv = Path(args.models)
    resources_csv = Path(args.resources)
    keywords_csv = Path(args.keywords)
    institutions_csv = Path(args.institutions)

    if models_csv.exists():
        write_json(DATA_DIR / "models.json", build_models(models_csv))
    if resources_csv.exists():
        write_json(DATA_DIR / "resources.json", build_resources(resources_csv))
    if keywords_csv.exists():
        write_json(DATA_DIR / "keywords.json", build_keywords(keywords_csv))
    if institutions_csv.exists():
        write_json(DATA_DIR / "institutions.json", build_institutions(institutions_csv))


if __name__ == "__main__":
    main()
