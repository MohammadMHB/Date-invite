FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PORT=8000 DATA_DIR=/data
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /data
VOLUME /data
EXPOSE 8000
CMD ["sh", "-c", "gunicorn app:application -b 0.0.0.0:${PORT:-8000} --workers 2 --access-logfile -"]
