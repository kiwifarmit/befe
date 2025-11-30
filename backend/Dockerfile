FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code is mounted via volume in docker-compose for dev
# COPY . . 

RUN groupadd -r appuser && useradd --no-log-init -r -g appuser -d /home/appuser -s /bin/bash appuser
RUN mkdir -p /home/appuser/app && chown -R appuser:appuser /home/appuser

WORKDIR /home/appuser/app

USER appuser 

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
