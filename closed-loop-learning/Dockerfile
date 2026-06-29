# Stage 1: Build Next.js frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend ./
RUN npm run build

# Stage 2: Python runtime with Node.js
FROM python:3.11-slim
WORKDIR /app

# Install Node.js runtime
RUN apt-get update && apt-get install -y curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --index-url https://pypi.org/simple -r requirements.txt

# Copy application code
COPY . .
RUN rm -rf frontend

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/frontend ./frontend

ENV PORT=8080
ENV PYTHONUNBUFFERED=1
EXPOSE 8080

# Start both FastAPI backend (port 8000) and Next.js frontend (port 8080)
CMD uvicorn api.main:app --host 127.0.0.1 --port 8000 & cd frontend && npm start -- -p 8080
