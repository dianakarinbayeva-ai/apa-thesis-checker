FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0
COPY . .
RUN useradd --create-home --uid 10001 apa && mkdir -p /data && chown apa:apa /data
USER apa
ENV APA_DATA_DIR=/data PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["gunicorn", "platform_config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]
