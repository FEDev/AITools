FROM python:3.11-slim
WORKDIR /app
COPY python /app/python
COPY mcp-server /app/mcp-server
RUN pip install --no-cache-dir -r /app/mcp-server/requirements.txt
WORKDIR /app/mcp-server
EXPOSE 8090
CMD ["python3", "server.py", "--http", "--port", "8090"]
