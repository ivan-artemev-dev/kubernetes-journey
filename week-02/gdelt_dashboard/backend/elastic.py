"""
Слой доступа к Elasticsearch: поиск, агрегации, аналитика по индексу gdelt_gkg.
"""
import os
import re
import datetime
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import BadRequestError
from dotenv import load_dotenv
from references import GCAM

load_dotenv()

ELASTIC_URL = os.getenv("ELASTIC_URL", "http://localhost:9200")
ELASTIC_INDEX = os.getenv("ELASTIC_INDEX", "gdelt_gkg")

_client = None

# Кэш того, какой вариант имени поля (обычное / .keyword) реально работает
# для агрегаций - заполняется по ходу первых запросов.
_field_variant_cache = {}


def get_client() -> Elasticsearch:
    global _client
    if _client is None:
        _client = Elasticsearch(ELASTIC_URL, request_timeout=60)
    return _client


def _agg_field(base: str) -> str:
    """Возвращает рабочее имя поля для terms-агрегации (с учётом .keyword)."""
    if base in _field_variant_cache:
        return _field_variant_cache[base]
    _field_variant_cache[base] = base
    return base


def _run_terms_agg(index: str, body_fn, field_base: str):
    """
    Выполняет агрегацию, при ошибке fielddata пробует field_base + '.keyword'
    и запоминает рабочий вариант.
    """
    field = _agg_field(field_base)
    try:
        return get_client().search(index=index, body=body_fn(field))
    except BadRequestError:
        alt = field_base if field.endswith(".keyword") else field_base + ".keyword"
        resp = get_client().search(index=index, body=body_fn(alt))
        _field_variant_cache[field_base] = alt
        return resp


def now_utc_str() -> str:
    return datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")


def days_ago_str(days: int) -> str:
    dt = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    return dt.strftime("%Y%m%d%H%M%S")


def hours_ago_str(hours: int) -> str:
    dt = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
    return dt.strftime("%Y%m%d%H%M%S")


def _day_histogram_agg(sub_aggs=None):
    """date проиндексирован как настоящий date-тип - группируем нативным date_histogram."""
    agg = {
        "date_histogram": {"field": "date", "calendar_interval": "day", "format": "yyyyMMdd"},
    }
    if sub_aggs:
        agg["aggs"] = sub_aggs
    return {"by_day": agg}


def get_feed(page: int = 1, size: int = 50):
    frm = (page - 1) * size
    resp = get_client().search(
        index=ELASTIC_INDEX,
        body={
            "from": frm,
            "size": size,
            "sort": [{"date": {"order": "desc"}}],
            "query": {"match_all": {}},
        },
    )
    hits = resp["hits"]["hits"]
    total = resp["hits"]["total"]["value"]
    return {
        "total": total,
        "page": page,
        "size": size,
        "items": [h["_source"] for h in hits],
    }


def _contains(field: str, value: str):
    """Регистронезависимый поиск подстроки в keyword-поле (в т.ч. массиве)."""
    return {"wildcard": {field: {"value": f"*{value.lower()}*", "case_insensitive": True}}}


def _date_range_filter(date_from: str = None, date_to: str = None):
    rng = {}
    if date_from:
        rng["gte"] = date_from
    if date_to:
        rng["lte"] = date_to
    if rng:
        return [{"range": {"date": rng}}]
    return []


def search_documents(q: str, search_type: str, date_from: str = None, date_to: str = None,
                      page: int = 1, size: int = 50):
    frm = (page - 1) * size
    must = []
    # url не индексируется (mapping index:false) - поиск по нему выполняется через
    # runtime-скрипт по _source, что означает полное сканирование совпавших
    # документов. Без ограничения периода это скан всего индекса и таймаут,
    # поэтому по умолчанию сужаем поиск URL до последних 24 часов.
    if search_type == "url" and not date_from and not date_to:
        date_from = hours_ago_str(24)
    filters = _date_range_filter(date_from, date_to)
    runtime_mappings = {}

    if search_type == "person":
        must.append(_contains("persons", q))
    elif search_type == "org":
        must.append(_contains("organizations", q))
    elif search_type == "theme":
        must.append({"term": {"themes": q.upper()}})
    elif search_type == "country":
        must.append({
            "nested": {
                "path": "locations",
                "query": {"term": {"locations.countrycode": q.upper()}},
            }
        })
    elif search_type == "source":
        must.append(_contains("source_name", q))
    elif search_type == "url":
        # url хранится с index:false - обычный запрос невозможен, а script query
        # не имеет доступа к _source (только runtime-поля его имеют). Поэтому
        # объявляем runtime-поле с нижним регистром url и ищем по нему wildcard'ом.
        runtime_mappings["url_rt"] = {
            "type": "keyword",
            "script": {
                "source": "def u = params._source['url']; if (u != null) { emit(u.toLowerCase()); }",
            },
        }
        must.append({"wildcard": {"url_rt": {"value": f"*{q.lower()}*"}}})
    else:
        must.append({
            "bool": {
                "should": [
                    _contains("persons", q),
                    _contains("organizations", q),
                    _contains("source_name", q),
                    {"term": {"themes": q.upper()}},
                ]
            }
        })

    body = {
        "from": frm,
        "size": size,
        "sort": [{"date": {"order": "desc"}}],
        "query": {"bool": {"must": must, "filter": filters}},
    }
    if runtime_mappings:
        body["runtime_mappings"] = runtime_mappings
    resp = get_client().search(index=ELASTIC_INDEX, body=body)
    return {
        "total": resp["hits"]["total"]["value"],
        "page": page,
        "size": size,
        "items": [h["_source"] for h in resp["hits"]["hits"]],
    }


def entity_analytics(entity_type: str, name: str, days: int = 30):
    field = "persons" if entity_type == "person" else "organizations"
    date_from = days_ago_str(days)
    base_query = {
        "bool": {
            "must": [_contains(field, name)],
            "filter": [{"range": {"date": {"gte": date_from}}}],
        }
    }

    resp = get_client().search(
        index=ELASTIC_INDEX,
        body={
            "size": 10,
            "sort": [{"date": {"order": "desc"}}],
            "query": base_query,
            "aggs": {
                **_day_histogram_agg({"avg_tone": {"avg": {"field": "tone.tone"}}}),
                "top_themes": {"terms": {"field": _agg_field("themes"), "size": 10}},
                "top_sources": {"terms": {"field": _agg_field("source_name"), "size": 10}},
                "top_countries": {
                    "nested": {"path": "locations"},
                    "aggs": {
                        "codes": {"terms": {"field": _agg_field("locations.countrycode"), "size": 10}}
                    },
                },
            },
        },
    )

    aggs = resp["aggregations"]
    by_day = [
        {
            "date": b["key_as_string"],
            "count": b["doc_count"],
            "avg_tone": round(b["avg_tone"]["value"], 2) if b["avg_tone"]["value"] is not None else None,
        }
        for b in aggs["by_day"]["buckets"]
    ]
    top_themes = [{"code": b["key"], "count": b["doc_count"]} for b in aggs["top_themes"]["buckets"]]
    top_sources = [{"source": b["key"], "count": b["doc_count"]} for b in aggs["top_sources"]["buckets"]]
    top_countries = [
        {"code": b["key"], "count": b["doc_count"]}
        for b in aggs["top_countries"]["codes"]["buckets"]
    ]

    return {
        "entity": name,
        "type": entity_type,
        "total": resp["hits"]["total"]["value"],
        "by_day": by_day,
        "top_themes": top_themes,
        "top_sources": top_sources,
        "top_countries": top_countries,
        "recent": [h["_source"] for h in resp["hits"]["hits"]],
    }


def trends(period: str = "24h"):
    if period == "7d":
        date_from = days_ago_str(7)
    elif period == "30d":
        date_from = days_ago_str(30)
    else:
        date_from = hours_ago_str(24)

    resp = get_client().search(
        index=ELASTIC_INDEX,
        body={
            "size": 0,
            "query": {"range": {"date": {"gte": date_from}}},
            "aggs": {
                "top_orgs": {"terms": {"field": _agg_field("organizations"), "size": 20}},
                "top_persons": {"terms": {"field": _agg_field("persons"), "size": 20}},
                "top_themes": {"terms": {"field": _agg_field("themes"), "size": 10}},
                "top_countries": {
                    "nested": {"path": "locations"},
                    "aggs": {
                        "codes": {"terms": {"field": _agg_field("locations.countrycode"), "size": 10}}
                    },
                },
            },
        },
    )
    aggs = resp["aggregations"]
    return {
        "period": period,
        "top_organizations": [{"name": b["key"], "count": b["doc_count"]} for b in aggs["top_orgs"]["buckets"]],
        "top_persons": [{"name": b["key"], "count": b["doc_count"]} for b in aggs["top_persons"]["buckets"]],
        "top_themes": [{"code": b["key"], "count": b["doc_count"]} for b in aggs["top_themes"]["buckets"]],
        "top_countries": [
            {"code": b["key"], "count": b["doc_count"]} for b in aggs["top_countries"]["codes"]["buckets"]
        ],
    }


def gcam_summary(country: str = None, date_from: str = None, date_to: str = None):
    must = []
    # gcam.* не индексируется - значения читаются скриптом по _source для каждого
    # документа, попавшего в агрегацию. Без ограничения периода это скан всего
    # индекса (миллионы документов) и таймаут, поэтому по умолчанию берём последние
    # 24 часа, если период не задан явно.
    if not date_from and not date_to:
        date_from = hours_ago_str(24)
    filters = _date_range_filter(date_from, date_to)
    if country:
        must.append({
            "nested": {
                "path": "locations",
                "query": {"term": {"locations.countrycode": country.upper()}},
            }
        })
    query = {"bool": {"must": must or [{"match_all": {}}], "filter": filters}}

    # Поле "gcam" в индексе замаплено как object с enabled:false - оно хранится
    # в _source, но не индексируется и недоступно для обычных агрегаций.
    # Поэтому читаем значения через runtime-поля со скриптом по _source.
    gcam_codes = list(GCAM.keys())
    runtime_mappings = {}
    aggs = {}
    for code in gcam_codes:
        fname = "gcam_" + re.sub(r"[^0-9a-zA-Z]", "_", code)
        runtime_mappings[fname] = {
            "type": "double",
            "script": {
                "source": (
                    "def g = params._source['gcam']; "
                    "if (g != null && g.containsKey(params.code)) { "
                    "  def v = g.get(params.code); "
                    "  if (v instanceof Number) { emit(((Number) v).doubleValue()); } "
                    "}"
                ),
                "params": {"code": code},
            },
        }
        aggs[fname] = {"avg": {"field": fname}}

    resp = get_client().search(
        index=ELASTIC_INDEX,
        body={
            "size": 0,
            "query": query,
            "runtime_mappings": runtime_mappings,
            "aggs": aggs,
        },
    )
    aggs_resp = resp["aggregations"]
    result = []
    for code in gcam_codes:
        fname = "gcam_" + re.sub(r"[^0-9a-zA-Z]", "_", code)
        val = aggs_resp.get(fname, {}).get("value")
        if val is not None:
            result.append({"code": code, "avg_value": round(val, 3)})
    return {
        "country": country,
        "total_docs": resp["hits"]["total"]["value"],
        "metrics": result,
    }


def map_points(date_from: str = None, date_to: str = None, theme: str = None):
    must = []
    filters = _date_range_filter(date_from, date_to)
    if theme:
        must.append({"term": {"themes": theme.upper()}})
    query = {"bool": {"must": must or [{"match_all": {}}], "filter": filters}}

    resp = get_client().search(
        index=ELASTIC_INDEX,
        body={
            "size": 0,
            "query": query,
            "aggs": {
                "locations": {
                    "nested": {"path": "locations"},
                    "aggs": {
                        "grid": {
                            "geohash_grid": {"field": "locations.location", "precision": 4},
                            "aggs": {
                                "centroid": {"geo_centroid": {"field": "locations.location"}},
                                "sample_name": {
                                    "terms": {"field": _agg_field("locations.fullname"), "size": 1}
                                },
                            },
                        }
                    },
                }
            },
        },
    )
    buckets = resp["aggregations"]["locations"]["grid"]["buckets"]
    points = []
    for b in buckets:
        centroid = b["centroid"]["location"]
        names = [x["key"] for x in b["sample_name"]["buckets"]]
        points.append({
            "lat": centroid["lat"],
            "lon": centroid["lon"],
            "count": b["doc_count"],
            "name": names[0] if names else "",
        })
    return {"points": points}


def map_publications_at(lat: float, lon: float, radius_km: float = 50,
                         date_from: str = None, date_to: str = None, size: int = 50):
    filters = _date_range_filter(date_from, date_to)
    query = {
        "bool": {
            "filter": filters + [{
                "nested": {
                    "path": "locations",
                    "query": {
                        "geo_distance": {
                            "distance": f"{radius_km}km",
                            "locations.location": {"lat": lat, "lon": lon},
                        }
                    },
                }
            }],
        }
    }
    resp = get_client().search(
        index=ELASTIC_INDEX,
        body={"size": size, "sort": [{"date": {"order": "desc"}}], "query": query},
    )
    return {"items": [h["_source"] for h in resp["hits"]["hits"]]}


def historical(days: int = 30, country: str = None, theme: str = None):
    date_from = days_ago_str(days)
    must = []
    if theme:
        must.append({"term": {"themes": theme.upper()}})
    if country:
        must.append({
            "nested": {
                "path": "locations",
                "query": {"term": {"locations.countrycode": country.upper()}},
            }
        })
    query = {
        "bool": {
            "must": must or [{"match_all": {}}],
            "filter": [{"range": {"date": {"gte": date_from}}}],
        }
    }
    resp = get_client().search(
        index=ELASTIC_INDEX,
        body={
            "size": 0,
            "query": query,
            "aggs": _day_histogram_agg({"avg_tone": {"avg": {"field": "tone.tone"}}}),
        },
    )
    buckets = resp["aggregations"]["by_day"]["buckets"]
    return {
        "days": days,
        "country": country,
        "theme": theme,
        "series": [
            {
                "date": b["key_as_string"],
                "count": b["doc_count"],
                "avg_tone": round(b["avg_tone"]["value"], 2) if b["avg_tone"]["value"] is not None else None,
            }
            for b in buckets
        ],
    }


def index_stats():
    client = get_client()
    count_resp = client.count(index=ELASTIC_INDEX)
    stats = {"total_documents": count_resp["count"]}
    try:
        resp = client.search(
            index=ELASTIC_INDEX,
            body={
                "size": 0,
                "aggs": {
                    "min_date": {"min": {"field": "date"}},
                    "max_date": {"max": {"field": "date"}},
                },
            },
        )
        stats["min_date"] = (
            resp["aggregations"]["min_date"].get("value_as_string")
            or resp["aggregations"]["min_date"].get("value")
        )
        stats["max_date"] = (
            resp["aggregations"]["max_date"].get("value_as_string")
            or resp["aggregations"]["max_date"].get("value")
        )
    except Exception:
        stats["min_date"] = None
        stats["max_date"] = None
    return stats
