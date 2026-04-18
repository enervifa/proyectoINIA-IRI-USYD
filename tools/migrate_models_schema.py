import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODELS_PATH = ROOT / "data" / "models.json"
KEYWORDS_PATH = ROOT / "data" / "keywords.json"
OLIMAR_GEOJSON = ROOT / "data" / "catchments" / "olimar.geojson"


def safe_list(value):
    return value if isinstance(value, list) else []


def compute_bbox_center(geojson_path: Path):
    try:
        gj = json.loads(geojson_path.read_text(encoding="utf-8"))
    except Exception:
        return None

    minx = miny = None
    maxx = maxy = None

    def walk_coords(coords):
        nonlocal minx, miny, maxx, maxy
        if not coords:
            return
        if isinstance(coords[0], (int, float)) and len(coords) >= 2:
            x, y = float(coords[0]), float(coords[1])
            minx = x if minx is None else min(minx, x)
            miny = y if miny is None else min(miny, y)
            maxx = x if maxx is None else max(maxx, x)
            maxy = y if maxy is None else max(maxy, y)
            return
        for c in coords:
            walk_coords(c)

    for feat in safe_list(gj.get("features")):
        geom = feat.get("geometry") or {}
        walk_coords(geom.get("coordinates"))

    if minx is None:
        return None
    return {"longitude": (minx + maxx) / 2.0, "latitude": (miny + maxy) / 2.0}


def main():
    # Some Windows editors write a UTF-8 BOM; accept it.
    models = json.loads(MODELS_PATH.read_text(encoding="utf-8-sig"))

    for model in models:
        # Remove fields we no longer use.
        model.pop("inputs", None)
        model.pop("institution", None)
        model.pop("gmic_member", None)

        # Collapse themes into a single field used everywhere.
        themes = (model.get("themes") or model.get("table_themes") or model.get("theme") or "").strip()
        model["themes"] = themes
        model.pop("table_themes", None)
        model.pop("theme", None)

    # Add Olimar if missing.
    if not any((m.get("name") or "").strip().lower() == "olimar" for m in models):
        max_id = max(int(m.get("id") or 0) for m in models) if models else 0
        max_order = max(int(m.get("table_order") or 0) for m in models) if models else 0
        center = compute_bbox_center(OLIMAR_GEOJSON) or {"latitude": -33.0, "longitude": -54.8}

        models.append(
            {
                "id": max_id + 1,
                "name": "Olimar",
                "themes": "Cantidad",
                "type": "Catchment",
                "scale": "Catchment",
                "status": "Active",
                "description": "Catchment boundary added from Olimar GeoJSON.",
                "website": "",
                "latitude": round(center["latitude"], 5),
                "longitude": round(center["longitude"], 5),
                "location": "Uruguay",
                "keywords": ["catchment", "hydrology"],
                "map_link": "data/catchments/olimar.geojson",
                "table_order": max_order + 1,
                "table_name": "Olimar",
                "table_scale": "Catchment",
                "swat_model": "SWAT 2012",
                "active_to_date": "",
                "show_in_catalogue": True,
            }
        )

    MODELS_PATH.write_text(json.dumps(models, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Ensure keywords entry exists for Olimar so it appears in the network.
    keywords = json.loads(KEYWORDS_PATH.read_text(encoding="utf-8-sig"))
    models_by_name = {str(m.get("name") or "").strip().lower(): m for m in models}
    olimar = models_by_name.get("olimar")
    if olimar:
        olimar_id = int(olimar.get("id"))
        if not any(int(k.get("model_id") or 0) == olimar_id for k in keywords):
            keywords.append(
                {
                    "model_id": olimar_id,
                    "catchment": "Olimar",
                    "keywords": ["cantidad de agua"],
                }
            )
            KEYWORDS_PATH.write_text(
                json.dumps(keywords, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )


if __name__ == "__main__":
    main()
