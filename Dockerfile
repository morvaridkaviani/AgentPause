# Multi-stage build for AgentPause. Targets:
#   backend   FastAPI + SQLite/PostgreSQL (port 8000)
#   frontend  Next.js standalone server (port 3000)
# docker compose builds both (see docker-compose.yml).

############################ backend ############################
FROM python:3.13-slim AS backend
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY sdk/python sdk/python
COPY simulator simulator
COPY backend backend
RUN pip install ./sdk/python ./simulator "./backend[postgres]" \
 && useradd --create-home --uid 10001 agentpause \
 && mkdir -p /data && chown agentpause /data
USER agentpause
ENV DATABASE_URL=sqlite:////data/agentpause.db \
    AGENTPAUSE_ENV=production
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health').status == 200 else 1)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

######################## frontend (build) ########################
FROM node:22-alpine AS frontend-build
WORKDIR /repo
COPY package.json package-lock.json ./
COPY frontend/package.json frontend/package.json
COPY sdk/typescript/package.json sdk/typescript/package.json
RUN npm ci --workspace frontend --include-workspace-root=false
COPY frontend frontend
# Rewrites to the API are compiled into the build, so BACKEND_URL must be known now.
ARG BACKEND_URL=http://backend:8000
ARG NEXT_PUBLIC_REPO_URL=
ENV BACKEND_URL=${BACKEND_URL} \
    NEXT_PUBLIC_REPO_URL=${NEXT_PUBLIC_REPO_URL} \
    NEXT_TELEMETRY_DISABLED=1
RUN npm run build --workspace frontend

########################### frontend ###########################
FROM node:22-alpine AS frontend
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0
# outputFileTracingRoot is the repository root, so the standalone server lives in frontend/.
COPY --from=frontend-build --chown=node:node /repo/frontend/.next/standalone ./
COPY --from=frontend-build --chown=node:node /repo/frontend/.next/static ./frontend/.next/static
USER node
EXPOSE 3000
CMD ["node", "frontend/server.js"]
