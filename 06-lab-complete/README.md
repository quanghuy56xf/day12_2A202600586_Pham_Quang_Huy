# Lab 12 — Complete Production Agent

Production-ready AI agent kết hợp tất cả concepts Day 12.

## Cấu trúc

```
06-lab-complete/
├── app/
│   ├── main.py           # FastAPI entry point
│   ├── config.py         # 12-factor config
│   ├── auth.py           # API Key authentication
│   ├── rate_limiter.py   # Redis sliding window (10 req/min)
│   ├── cost_guard.py     # Monthly budget guard ($10/user)
│   └── session.py        # Conversation history (Redis)
├── utils/mock_llm.py
├── Dockerfile            # Multi-stage, non-root, HEALTHCHECK
├── docker-compose.yml    # agent + redis + nginx
├── nginx.conf
├── railway.toml
├── render.yaml
├── .env.example
└── check_production_ready.py
```

## Chạy local (Docker Compose)

```bash
cd 06-lab-complete
cp .env.example .env.local
# Chỉnh AGENT_API_KEY trong .env.local nếu cần

docker compose up --build
```

## Test endpoints

```bash
# Health (public)
curl http://localhost/health

# Ready (public)
curl http://localhost/ready

# Ask — cần API key
curl -X POST http://localhost/ask \
  -H "X-API-Key: lab-secret-key-2026" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"What is Docker?"}'

# Không có key → 401
curl -X POST http://localhost/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello"}'
```

## Scale với load balancer

```bash
docker compose up --build --scale agent=3
```

## Kiểm tra production readiness

```bash
$env:PYTHONIOENCODING="utf-8"
python check_production_ready.py
```

## Deploy cloud

**Railway:**
```bash
npm i -g @railway/cli
railway login
railway init
railway variables set AGENT_API_KEY=<secret>
railway variables set REDIS_URL=<redis-url>
railway up
railway domain
```

**Render:** Push repo → Dashboard → New Blueprint → connect repo (đọc `render.yaml`).

## Environment variables

| Variable | Default | Mô tả |
|----------|---------|-------|
| `AGENT_API_KEY` | — | API key bắt buộc cho `/ask` |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis cho session, rate limit, budget |
| `RATE_LIMIT_PER_MINUTE` | `10` | Giới hạn request/phút/user |
| `MONTHLY_BUDGET_USD` | `10.0` | Budget LLM/tháng/user |
| `ENVIRONMENT` | `development` | `production` bật validation secrets |
