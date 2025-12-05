# SEC EDGAR MCP Server
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY server.py .
COPY company-tickers.json .
COPY favicon.ico .

# Cloud Run configuration
EXPOSE 8080
ENV PORT=8080
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

CMD ["python", "server.py"]
