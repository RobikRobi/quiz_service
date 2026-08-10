# quiz_service

Standalone FastAPI service for quizzes.

## Local Docker

```bash
cp .env.example .env
docker compose build
docker compose run --rm migrate
docker compose up -d api
```

API docs:

```text
http://localhost:8002/docs
```

## Auth Boundary

The service is intentionally independent from `user_service`. Endpoints that need a user id read it from:

```http
X-User-Id: <uuid>
```

Later, the gateway or frontend can pass this value after validating the user token.

## Production

Set `QUIZ_DATABASE_URL` in `.env.prod`, then run:

```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml run --rm migrate
docker compose -f docker-compose.prod.yml up -d api
```
