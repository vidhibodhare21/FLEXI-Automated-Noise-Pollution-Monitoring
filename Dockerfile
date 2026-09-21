FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt requirements-dashboard.txt .
RUN pip install --no-cache-dir -r requirements-dashboard.txt
COPY . .
EXPOSE 7860
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-7860}"]
