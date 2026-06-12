# Deployment Information

## Public URL

**Live (tunnel):** https://small-pillows-wish.loca.lt

> Tunnel phục vụ demo nhanh. URL thay đổi mỗi lần chạy `npx localtunnel --port 80`.
> Deploy vĩnh viễn: dùng Render Blueprint (xem bên dưới).

**Permanent (Render):** Sau khi connect Blueprint trên Render Dashboard, URL dạng:
`https://ai-agent-production.onrender.com` (cập nhật sau deploy)

## Platform

| Môi trường | Platform |
|-----------|----------|
| Local dev | Docker Compose + Nginx |
| Demo public | Localtunnel → port 80 |
| Production | **Render Blueprint** (`render.yaml` ở repo root) |

## Environment Variables Set

| Variable | Value |
|----------|-------|
| `PORT` | `8000` (Railway/Render inject) |
| `REDIS_URL` | `redis://redis:6379/0` (local) / Render Redis add-on |
| `AGENT_API_KEY` | `lab-secret-key-2026` (local) / auto-generated (Render) |
| `RATE_LIMIT_PER_MINUTE` | `10` |
| `MONTHLY_BUDGET_USD` | `10.0` |
| `ENVIRONMENT` | `staging` (local) / `production` (cloud) |

## Test Commands

### Health Check

```bash
curl -H "Bypass-Tunnel-Reminder: true" https://small-pillows-wish.loca.lt/health
# Expected: {"status":"ok",...}
```

### Readiness Check

```bash
curl -H "Bypass-Tunnel-Reminder: true" https://small-pillows-wish.loca.lt/ready
# Expected: {"ready":true,"redis":"connected"}
```

### Authentication required (401)

```bash
curl -X POST https://small-pillows-wish.loca.lt/ask \
  -H "Bypass-Tunnel-Reminder: true" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello"}'
# Expected: HTTP 401
```

### API Test (with authentication)

```bash
curl -X POST https://small-pillows-wish.loca.lt/ask \
  -H "Bypass-Tunnel-Reminder: true" \
  -H "X-API-Key: lab-secret-key-2026" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello"}'
# Expected: HTTP 200 with answer JSON
```

## Deploy to Render (Recommended — permanent URL)

1. Repo đã push lên GitHub: `https://github.com/quanghuy56xf/day12_2A202600586_Pham_Quang_Huy`
2. [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**
3. Connect GitHub repo → Render đọc `render.yaml` (root)
4. Approve deploy → Render tạo Web Service + Redis
5. Copy public URL vào file này

## Deploy to Railway (Alternative)

```bash
npm i -g @railway/cli
cd 06-lab-complete
railway login
railway init
railway add --plugin redis
railway variables set ENVIRONMENT=production
railway variables set RATE_LIMIT_PER_MINUTE=10
railway variables set MONTHLY_BUDGET_USD=10.0
railway up
railway domain
```

## Screenshots

| File | Mô tả |
|------|-------|
| [screenshots/docker-compose-running.png](screenshots/docker-compose-running.png) | Docker services running |
| [screenshots/health-check.png](screenshots/health-check.png) | `/health` response |
| [screenshots/auth-test.png](screenshots/auth-test.png) | 401 vs 200 auth test |
| [screenshots/rate-limit-test.png](screenshots/rate-limit-test.png) | Rate limit 429 |
| [screenshots/production-ready-check.png](screenshots/production-ready-check.png) | 20/20 checks |
| [screenshots/cloud-dashboard.png](screenshots/cloud-dashboard.png) | Public URL / deploy |

## Verified Test Results

```
check_production_ready.py: 20/20 (100%)
Health: HTTP 200 | Ready: HTTP 200
No API key: HTTP 401 | With key: HTTP 200
Rate limit: HTTP 200 x10 → 429
Public tunnel /health: HTTP 200
Docker image: 307 MB
```

## Self-Test Checklist

- [x] `/health` returns 200
- [x] `/ready` returns 200 when Redis connected
- [x] `/ask` without key returns 401
- [x] `/ask` with key returns 200
- [x] Rate limit triggers 429 after 10 requests/minute
- [x] `python check_production_ready.py` passes
- [x] No `.env` committed (only `.env.example`)
- [x] Multi-stage Dockerfile, image < 500 MB
- [x] Public URL accessible (localtunnel demo)
- [x] Render Blueprint ready at repo root
