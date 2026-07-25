"""
GDELT Analytics Dashboard - FastAPI backend.
"""
import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

import elastic
import references

load_dotenv()

app = FastAPI(title="GDELT Analytics Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _decorate_doc(doc: dict) -> dict:
    """Добавляет расшифровки тем и стран к документу для фронтенда."""
    doc = dict(doc)
    themes = doc.get("themes") or []
    doc["themes_ru"] = references.decode_themes(themes[:5])
    locations = doc.get("locations") or []
    if locations:
        doc["country_ru"] = references.decode_country(locations[0].get("countrycode"))
    else:
        doc["country_ru"] = None
    return doc


@app.get("/api/feed")
def api_feed(page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=200)):
    result = elastic.get_feed(page=page, size=size)
    result["items"] = [_decorate_doc(d) for d in result["items"]]
    return result


@app.get("/api/search")
def api_search(
    q: str = Query(..., min_length=1),
    type: str = Query(..., pattern="^(person|org|theme|country|source|url)$"),
    from_: Optional[str] = Query(None, alias="from"),
    to: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
):
    result = elastic.search_documents(q=q, search_type=type, date_from=from_, date_to=to, page=page, size=size)
    result["items"] = [_decorate_doc(d) for d in result["items"]]
    return result


@app.get("/api/entity/{entity_type}/{name}")
def api_entity(entity_type: str, name: str, days: int = Query(30, ge=1, le=365)):
    if entity_type not in ("person", "org"):
        raise HTTPException(status_code=400, detail="entity_type должен быть 'person' или 'org'")
    result = elastic.entity_analytics(entity_type, name, days=days)
    result["top_themes"] = [
        {"code": t["code"], "name_ru": references.decode_theme(t["code"]), "count": t["count"]}
        for t in result["top_themes"]
    ]
    result["top_countries"] = [
        {"code": c["code"], "name_ru": references.decode_country(c["code"]), "count": c["count"]}
        for c in result["top_countries"]
    ]
    result["recent"] = [_decorate_doc(d) for d in result["recent"]]
    return result


@app.get("/api/trends")
def api_trends(period: str = Query("24h", pattern="^(24h|7d|30d)$")):
    result = elastic.trends(period=period)
    result["top_themes"] = [
        {"code": t["code"], "name_ru": references.decode_theme(t["code"]), "count": t["count"]}
        for t in result["top_themes"]
    ]
    result["top_countries"] = [
        {"code": c["code"], "name_ru": references.decode_country(c["code"]), "count": c["count"]}
        for c in result["top_countries"]
    ]
    return result


@app.get("/api/gcam/summary")
def api_gcam_summary(country: Optional[str] = None, from_: Optional[str] = Query(None, alias="from"), to: Optional[str] = None):
    result = elastic.gcam_summary(country=country, date_from=from_, date_to=to)
    decorated = []
    for m in result["metrics"]:
        info = references.decode_gcam(m["code"])
        decorated.append({**m, "name_ru": info["name_ru"], "category": info["category"]})
    result["metrics"] = decorated
    return result


@app.get("/api/gcam/catalog")
def api_gcam_catalog():
    return {"items": references.list_gcam_catalog()}


@app.get("/api/map")
def api_map(from_: Optional[str] = Query(None, alias="from"), to: Optional[str] = None, theme: Optional[str] = None):
    return elastic.map_points(date_from=from_, date_to=to, theme=theme)


@app.get("/api/map/point")
def api_map_point(
    lat: float,
    lon: float,
    radius_km: float = 50,
    from_: Optional[str] = Query(None, alias="from"),
    to: Optional[str] = None,
):
    result = elastic.map_publications_at(lat=lat, lon=lon, radius_km=radius_km, date_from=from_, date_to=to)
    result["items"] = [_decorate_doc(d) for d in result["items"]]
    return result


@app.get("/api/historical")
def api_historical(
    days: int = Query(30, ge=1, le=365),
    country: Optional[str] = None,
    theme: Optional[str] = None,
):
    return elastic.historical(days=days, country=country, theme=theme)


@app.get("/api/stats")
def api_stats():
    return elastic.index_stats()


@app.get("/api/health")
def api_health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("BACKEND_HOST", "0.0.0.0"),
        port=int(os.getenv("BACKEND_PORT", "8000")),
        reload=True,
    )
