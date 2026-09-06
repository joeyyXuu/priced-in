FROM python:3.13-slim
WORKDIR /app
COPY api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY api /app/api
COPY web /app/web
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
