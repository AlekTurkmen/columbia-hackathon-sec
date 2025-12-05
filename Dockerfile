# Dockerfile for SEC MCP Server
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and data files
COPY remote-mcp-boilerplate.py .
COPY company-tickers.json .

# Expose port 8080 (Cloud Run default)
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

# Run the MCP server
CMD ["python", "remote-mcp-boilerplate.py"]

