FROM node:22-bookworm-slim AS frontend
WORKDIR /build/web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 HYDROFLY_WEB=/app/dist NUMBA_CACHE_DIR=/tmp/numba-cache
COPY requirements-lock.txt pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir -r requirements-lock.txt && pip install --no-deps .
COPY --from=frontend /build/dist ./dist
RUN useradd --create-home --uid 10001 hydrofly
USER hydrofly
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "hydrofly.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
