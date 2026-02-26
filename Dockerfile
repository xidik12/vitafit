# Stage 1: Build React frontend
FROM node:20.18.1-slim AS frontend-build
WORKDIR /webapp
COPY webapp/package.json webapp/package-lock.json ./
RUN npm ci
COPY webapp/ .
RUN npm run build

# Stage 2: Python backend + serve frontend
FROM python:3.12.8-slim
WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn==23.0.0

# Copy backend code
COPY backend/ .

# Copy built frontend
COPY --from=frontend-build /webapp/dist /webapp/dist

# Railway provides PORT env var
ENV PORT=8000
EXPOSE 8000

CMD gunicorn app.main:app -k uvicorn.workers.UvicornWorker --workers 1 --bind 0.0.0.0:${PORT} --timeout 120 --graceful-timeout 30
