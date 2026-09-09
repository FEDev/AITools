FROM python:3.11-slim
WORKDIR /app
COPY python /app/python
COPY tools-manifest /app/tools-manifest
COPY rest-api /app/rest-api
RUN pip install --no-cache-dir -r /app/rest-api/requirements.txt
WORKDIR /app/rest-api
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
