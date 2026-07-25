FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY gdelt_parser.py .
COPY 03_pipeline.py .
COPY 02_create_index.py .

RUN mkdir -p /app/downloads

ENV ES_HOST=http://elasticsearch:9200

CMD ["python", "03_pipeline.py"]
