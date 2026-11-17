# Stage 1: Build Tailwind CSS and bundle HTMX locally (100% offline runtime)
FROM docker.io/library/node:20-alpine AS assets
WORKDIR /build
COPY package.json tailwind.config.js ./
COPY app/static/css/input.css ./app/static/css/input.css
COPY app/templates ./app/templates
RUN npm install --no-audit --no-fund && \
    npm run build:css && \
    mkdir -p /build/app/static/js && \
    cp node_modules/htmx.org/dist/htmx.min.js /build/app/static/js/htmx.min.js

# Stage 2: FastAPI Python runtime
FROM docker.io/library/python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY --from=assets /build/app/static/css/app.css ./app/static/css/app.css
COPY --from=assets /build/app/static/js/htmx.min.js ./app/static/js/htmx.min.js

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
