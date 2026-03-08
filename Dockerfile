# ============================================
# Zephyr — UI Intelligence Platform
# Multi-stage Docker build
# ============================================

# --- Stage 1: Build Vue Frontend ---
FROM node:20-alpine AS frontend-build

WORKDIR /app/zephyr_ui
COPY zephyr_ui/package.json zephyr_ui/package-lock.json* ./
RUN npm ci --no-audit
COPY zephyr_ui/ .
RUN npm run build

# --- Stage 2: Python Backend ---
FROM python:3.11-slim

# System dependencies for Playwright + Lighthouse
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gnupg wget unzip \
    libnss3 libatk-bridge2.0-0 libdrm2 libxcomposite1 libxdamage1 \
    libxrandr2 libgbm1 libasound2 libpangocairo-1.0-0 libgtk-3-0 \
    libx11-xcb1 libxshmfence1 fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Node.js for Lighthouse
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g lighthouse

WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium --with-deps

# Copy backend code
COPY config/ config/
COPY core/ core/
COPY agents/ agents/
COPY orchestrator/ orchestrator/
COPY api/ api/
COPY mcp_server/ mcp_server/

# Copy built frontend
COPY --from=frontend-build /app/zephyr_ui/dist zephyr_ui/dist

# Create directories
RUN mkdir -p reports screenshots baselines

# Non-root user for security
RUN useradd -r -s /bin/false zephyr && \
    chown -R zephyr:zephyr /app
USER zephyr

# Environment
ENV ZEPHYR_HOST=0.0.0.0
ENV ZEPHYR_PORT=8000

EXPOSE 8000

CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]
