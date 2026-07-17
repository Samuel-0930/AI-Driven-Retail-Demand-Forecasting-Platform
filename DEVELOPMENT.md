# Local development

## Prerequisites

- Python 3.11
- Node.js 20+
- Docker Desktop with Docker Compose

## Backend

```bash
uv venv venv --python 3.11
uv pip install --python venv/bin/python -r backend/requirements.txt
PYTHONPATH=. venv/bin/pytest -q backend/tests
PYTHONPATH=. venv/bin/uvicorn backend.main:app --reload
```

## Frontend

```bash
cd frontend
npm ci
npm run lint
npm run build
npm run dev
```

The development server proxies `/api` and `/health` to `http://127.0.0.1:8000`. Set `BACKEND_URL` before `npm run dev` to use another backend.

## Full stack

```bash
cp .env.example .env
docker compose up --build
docker compose exec backend python backend/train_baseline.py
```

The repository does not contain trained model artifacts. Train at least one store/product model before using the prediction form.
