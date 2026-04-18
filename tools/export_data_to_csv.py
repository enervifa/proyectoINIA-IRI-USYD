import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SOURCE_DIR = DATA_DIR / "source"

MODELS_PATH = DATA_DIR / "models.json"
RESOURCES_PATH = DATA_DIR / "resources.json"
KEYWORDS_PATH = DATA_DIR / "keywords.json"
INSTITUTIONS_PATH = DATA_DIR / "institutions.json"


MODELS_COLUMNS = [
    "id",
    "nombre",
    "temas",
    "tipo",
    "escala",
    "estado",
    "descripcion",
    "sitio_web",
    "latitud",
    "longitud",
    "ubicacion",
    "palabras_clave",
    "enlace_mapa",
    "orden_tabla",
    "nombre_tabla",
    "escala_tabla",
    "modelo_swat",
    "activo_a_la_fecha",
    "mostrar_en_catalogo",
]

RESOURCES_COLUMNS = ["model_id", "catchment", "type", "title", "url", "authors", "year"]
KEYWORDS_COLUMNS = ["model_id", "catchment", "keywords"]
INSTITUTIONS_COLUMNS = ["name", "url"]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_csv(path: Path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Excel on Windows opens UTF-8 CSV reliably when it has a BOM.
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def join_list(value):
    if not isinstance(value, list):
        return ""
    return "; ".join(str(v).strip() for v in value if str(v).strip())


def translate_status(value: str) -> str:
    v = (value or "").strip()
    if v.lower() == "active":
        return "Activo"
    if v.lower() == "inactive":
        return "Inactivo"
    return v


def translate_type(value: str) -> str:
    v = (value or "").strip()
    key = v.lower()
    mapping = {
        "catchment": "Cuenca",
        "basin": "Cuenca",
        "lagoon": "Laguna",
        "experimental site": "Sitio experimental",
    }
    return mapping.get(key, v)


def translate_scale(value: str) -> str:
    v = (value or "").strip()
    key = v.lower()
    mapping = {
        "catchment": "Cuenca",
        "basin": "Cuenca",
        "lagoon": "Laguna",
        "lagoon catchment": "Cuenca de laguna",
        "plot / small catchment": "Parcela / microcuenca",
    }
    return mapping.get(key, v)


def export_models():
    models = read_json(MODELS_PATH)
    rows = []
    for m in models:
        row = {
            "id": m.get("id", ""),
            "nombre": m.get("name", ""),
            "temas": m.get("themes", ""),
            "tipo": translate_type(m.get("type", "")),
            "escala": translate_scale(m.get("scale", "")),
            "estado": translate_status(m.get("status", "")),
            "descripcion": m.get("description", ""),
            "sitio_web": m.get("website", ""),
            "latitud": m.get("latitude", ""),
            "longitud": m.get("longitude", ""),
            "ubicacion": m.get("location", ""),
            "palabras_clave": join_list(m.get("keywords")),
            "enlace_mapa": m.get("map_link", ""),
            "orden_tabla": m.get("table_order", ""),
            "nombre_tabla": m.get("table_name", ""),
            "escala_tabla": translate_scale(m.get("table_scale", "")),
            "modelo_swat": m.get("swat_model", ""),
            "activo_a_la_fecha": m.get("active_to_date", ""),
            "mostrar_en_catalogo": "si" if bool(m.get("show_in_catalogue", True)) else "no",
        }
        rows.append(row)

    rows.sort(key=lambda r: (int(r["orden_tabla"] or 10**9), int(r["id"] or 10**9), str(r["nombre"])))
    write_csv(SOURCE_DIR / "models.csv", MODELS_COLUMNS, rows)


def export_resources():
    resources = read_json(RESOURCES_PATH)
    rows = []
    for entry in resources:
        model_id = entry.get("model_id", "")
        catchment = entry.get("catchment", "")
        for item in entry.get("items") or []:
            rows.append(
                {
                    "model_id": model_id,
                    "catchment": catchment,
                    "type": item.get("type", ""),
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "authors": item.get("authors", ""),
                    "year": item.get("year", ""),
                }
            )

    rows.sort(
        key=lambda r: (
            (r["model_id"] is None) or (r["model_id"] == ""),
            int(r["model_id"] or 10**9),
            str(r["catchment"] or ""),
            str(r["year"] or ""),
            str(r["title"] or ""),
        )
    )
    write_csv(SOURCE_DIR / "resources.csv", RESOURCES_COLUMNS, rows)


def export_keywords():
    keywords = read_json(KEYWORDS_PATH)
    rows = []
    for entry in keywords:
        rows.append(
            {
                "model_id": entry.get("model_id", ""),
                "catchment": entry.get("catchment", ""),
                "keywords": join_list(entry.get("keywords")),
            }
        )

    rows.sort(
        key=lambda r: (
            (r["model_id"] is None) or (r["model_id"] == ""),
            int(r["model_id"] or 10**9),
            str(r["catchment"] or ""),
        )
    )
    write_csv(SOURCE_DIR / "keywords.csv", KEYWORDS_COLUMNS, rows)


def export_institutions():
    institutions = read_json(INSTITUTIONS_PATH)
    rows = [{"name": i.get("name", ""), "url": i.get("url", "")} for i in institutions]
    rows.sort(key=lambda r: str(r["name"] or ""))
    write_csv(SOURCE_DIR / "institutions.csv", INSTITUTIONS_COLUMNS, rows)


def main():
    errors = []

    try:
        export_models()
    except PermissionError as exc:
        errors.append(str(exc))

    try:
        export_resources()
    except PermissionError as exc:
        errors.append(str(exc))

    try:
        export_keywords()
    except PermissionError as exc:
        errors.append(str(exc))

    try:
        export_institutions()
    except PermissionError as exc:
        errors.append(str(exc))

    if errors:
        raise SystemExit(
            "Algunos CSV no se pudieron escribir porque estan en uso (Excel). "
            "Cierra los archivos y reintenta.\n"
            + "\n".join(f"- {e}" for e in errors)
        )


if __name__ == "__main__":
    main()
