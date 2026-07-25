FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV ELASTIC_URL=http://elasticsearch:9200
ENV ELASTIC_INDEX=gdelt_gkg
ENV BACKEND_HOST=0.0.0.0
ENV BACKEND_PORT=8000

EXPOSE 8000

CMD ["python", "main.py"]
