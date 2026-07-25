#!/usr/bin/env python3
"""
GDELT V2 GKG Pipeline с автодогоном пропусков.

Логика:
- Скачивает мастер-лист всех V2 GKG файлов
- Проверяет какие уже загружены в Elastic (по record_id)
- Скачивает и загружает все недостающие
- Запускать по cron каждые 15-20 минут

crontab:
*/20 * * * * /home/user/Desktop/gdelt/venv/bin/python3 /home/user/Desktop/gdelt/03_pipeline.py >> /home/user/Desktop/gdelt/pipeline.log 2>&1
"""

import requests
import zipfile
import io
import csv
import logging
import os
import urllib3
from datetime import datetime, timezone, timedelta
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from gdelt_parser import row_to_doc

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
csv.field_size_limit(10 * 1024 * 1024)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
log = logging.getLogger(__name__)

es = Elasticsearch(os.environ.get("ES_HOST", "http://localhost:9200"))
INDEX = "gdelt_gkg"
DOWNLOAD_DIR = os.path.expanduser("~/Desktop/gdelt/downloads")
BATCH_SIZE = 1000

# Сколько дней назад смотреть при старте
LOOKBACK_DAYS = 30

MASTERLIST_URL = "http://data.gdeltproject.org/gdeltv2/masterfilelist.txt"


def get_masterlist(days=LOOKBACK_DAYS):
    """Скачиваем мастер-лист и фильтруем GKG файлы за последние N дней."""
    log.info("Скачиваем мастер-лист...")
    try:
        resp = requests.get(MASTERLIST_URL, timeout=60, verify=False)
        resp.raise_for_status()
    except Exception as e:
        log.error(f"Ошибка скачивания мастер-листа: {e}")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    files = []

    for line in resp.text.splitlines():
        parts = line.strip().split(' ')
        if len(parts) < 3:
            continue
        size, md5, url = parts[0], parts[1], parts[2]
        # Берём только GKG файлы (не mentions, не export)
        if '.gkg.csv.zip' not in url:
            continue
        # Извлекаем дату из имени файла: ...gdeltv2/20260720153000.gkg.csv.zip
        fname = url.split('/')[-1]
        date_part = fname.replace('.gkg.csv.zip', '')
        if len(date_part) != 14 or not date_part.isdigit():
            continue
        try:
            file_dt = datetime.strptime(date_part, '%Y%m%d%H%M%S').replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if file_dt >= cutoff:
            files.append((date_part, url))

    log.info(f"Найдено {len(files)} GKG файлов за последние {days} дней")
    return files


def is_loaded(date_part):
    """Проверяем есть ли файл уже в Elastic по record_id префиксу."""
    try:
        resp = es.count(index=INDEX, query={
            "prefix": {"record_id": date_part}
        })
        return resp['count'] > 0
    except Exception:
        return False


def load_file(date_part, url):
    """Скачиваем и загружаем один GKG файл."""
    zip_path = os.path.join(DOWNLOAD_DIR, f"{date_part}.gkg.csv.zip")

    # Скачиваем если нет локально
    if not os.path.exists(zip_path):
        try:
            resp = requests.get(url, timeout=180, verify=False)
            if resp.status_code == 404:
                log.warning(f"Файл не найден: {url}")
                return 0
            resp.raise_for_status()
            with open(zip_path, 'wb') as f:
                f.write(resp.content)
            log.info(f"Скачан: {date_part} ({len(resp.content)//1024}KB)")
        except Exception as e:
            log.error(f"Ошибка скачивания {date_part}: {e}")
            return 0

    # Парсим и грузим в Elastic
    docs_loaded = 0
    batch = []

    try:
        with zipfile.ZipFile(zip_path) as zf:
            fname = zf.namelist()[0]
            with zf.open(fname) as f:
                reader = csv.reader(
                    io.TextIOWrapper(f, encoding='utf-8', errors='replace'),
                    delimiter='\t'
                )
                for row in reader:
                    doc = row_to_doc(row)
                    if doc:
                        batch.append({"_index": INDEX, "_source": doc})

                    if len(batch) >= BATCH_SIZE:
                        ok, errors = bulk(es, batch, raise_on_error=False)
                        docs_loaded += ok
                        if errors:
                            log.warning(f"{len(errors)} ошибок при bulk")
                        batch = []

        if batch:
            ok, _ = bulk(es, batch, raise_on_error=False)
            docs_loaded += ok

    except Exception as e:
        log.error(f"Ошибка парсинга {date_part}: {e}")
        # Удаляем битый файл чтобы перескачать в следующий раз
        os.remove(zip_path)
        return 0

    # Удаляем архив после загрузки чтобы не копить гигабайты
    # Закомментируй если хочешь хранить архивы
    # os.remove(zip_path)

    log.info(f"Загружено {docs_loaded} документов из {date_part}")
    return docs_loaded


def run():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # При первом запуске грузим за 30 дней, потом только новые
    # Определяем lookback: если индекс пустой — 30 дней, иначе 1 день
    try:
        total = es.count(index=INDEX)['count']
        days = LOOKBACK_DAYS if total == 0 else 1
    except Exception:
        days = LOOKBACK_DAYS

    log.info(f"=== GDELT Pipeline запуск, lookback={days}d ===")

    files = get_masterlist(days=days)
    if not files:
        log.warning("Мастер-лист пуст или недоступен")
        return

    # Сортируем от старых к новым
    files.sort(key=lambda x: x[0])

    loaded_total = 0
    skipped = 0

    for date_part, url in files:
        if is_loaded(date_part):
            skipped += 1
            continue
        count = load_file(date_part, url)
        loaded_total += count

    log.info(f"=== Готово: загружено {loaded_total} документов, пропущено {skipped} файлов ===")


if __name__ == '__main__':
    run()
