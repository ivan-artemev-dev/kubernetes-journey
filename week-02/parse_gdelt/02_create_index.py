#!/usr/bin/env python3
import os
from elasticsearch import Elasticsearch

es = Elasticsearch(os.environ.get("ES_HOST", "http://localhost:9200"))
INDEX = "gdelt_gkg"

if es.indices.exists(index=INDEX):
    print(f"Индекс {INDEX} существует, удаляем...")
    es.indices.delete(index=INDEX)

es.indices.create(
    index=INDEX,
    settings={
        "number_of_shards": 3,
        "number_of_replicas": 0,
        "refresh_interval": "30s",
    },
    mappings={
        "properties": {
            "record_id":     {"type": "keyword"},
            "date":          {"type": "date", "format": "yyyyMMddHHmmss||yyyyMMdd"},
            "source_name":   {"type": "keyword"},
            "url":           {"type": "keyword", "index": False},

            # Темы
            "themes":        {"type": "keyword"},

            # Локации
            "locations": {
                "type": "nested",
                "properties": {
                    "geo_type":    {"type": "integer"},
                    "fullname":    {"type": "keyword"},
                    "countrycode": {"type": "keyword"},
                    "adm1code":    {"type": "keyword"},
                    "adm2code":    {"type": "keyword"},
                    "location":    {"type": "geo_point"},
                }
            },

            # Сущности
            "persons":       {"type": "keyword"},
            "organizations": {"type": "keyword"},
            "all_names":     {"type": "keyword"},

            # Тональность
            "tone": {
                "properties": {
                    "tone":     {"type": "float"},
                    "positive": {"type": "float"},
                    "negative": {"type": "float"},
                    "polarity": {"type": "float"},
                    "activity": {"type": "float"},
                    "selfref":  {"type": "float"},
                }
            },

            # Цитаты
            "quotations": {
                "type": "nested",
                "properties": {
                    "speaker": {"type": "keyword"},
                    "quote":   {"type": "text"},
                }
            },

            # Числа/суммы из текста
            "amounts": {
                "type": "nested",
                "properties": {
                    "amount": {"type": "float"},
                    "object": {"type": "keyword"},
                }
            },

            # GCAM психолингвистика — храним как flat object
            "gcam": {"type": "object", "enabled": False},  # не индексируем, только храним

            # Картинки
            "sharing_image":  {"type": "keyword", "index": False},

            # Язык оригинала
            "translation_info": {"type": "keyword"},

            # Сырые поля
            "raw_themes":    {"type": "text", "index": False},
            "raw_locations": {"type": "text", "index": False},
            "raw_counts":    {"type": "text", "index": False},
        }
    }
)
print(f"✅ Индекс {INDEX} создан с V2 маппингом")
