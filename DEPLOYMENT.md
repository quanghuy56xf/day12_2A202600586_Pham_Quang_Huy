# Deployment Information

## Public URL (Railway)

**Railway:** _(cập nhật sau `railway domain`)_

Ví dụ: `https://ai-agent-production.up.railway.app`

## Platform

| Môi trường | Platform |
|-----------|----------|
| Local dev | Docker Compose + Nginx |
| Production | **Railway** (Docker + Redis plugin) |

## Environment Variables

| Variable | Giá trị |
|----------|---------|
| `ENVIRONMENT` | `production` |
| `AGENT_API_KEY` | secret (Railway Dashboard / CLI) |
| `JWT_SECRET` | secret |
| `REDIS_URL` | từ Redis plugin Railway |
| `RATE_LIMIT_PER_MINUTE` | `10` |
| `MONTHLY_BUDGET_USD` | `10.0` |
| `PORT` | Railway inject tự động |

## Deploy Railway

### Cách 1 — GitHub (khuyến nghị)

1. [Railway Dashboard](https://railway.app) → **New Project** → **Deploy from GitHub repo**
2. Chọn repo: `quanghuy56xf/day12_2A202600586_Pham_Quang_Huy`
3. **Settings → Root Directory:** `06-lab-complete`
4. **New → Database → Add Redis** (link vào service agent)
5. Service agent → **Variables:**
   - `ENVIRONMENT=production`
   - `AGENT_API_KEY=<your-secret-key>`
   - `JWT_SECRET=<your-jwt-secret>`
   - `REDIS_URL=${{Redis.REDIS_URL}}` (hoặc reference Redis service)
   - `RATE_LIMIT_PER_MINUTE=10`
   - `MONTHLY_BUDGET_USD=10.0`
6. **Deploy** → copy public URL

### Cách 2 — Railway CLI

```bash
npm i -g @railway/cli
cd 06-lab-complete
railway login
railway init
railway add --plugin redis
railway variables set ENVIRONMENT=production
railway variables set AGENT_API_KEY=your-secret-key
railway variables set JWT_SECRET=your-jwt-secret
railway variables set RATE_LIMIT_PER_MINUTE=10
railway variables set MONTHLY_BUDGET_USD=10.0
# Link REDIS_URL từ Redis service trong Dashboard hoặc:
# railway variables set REDIS_URL=<redis-url-from-dashboard>
railway up
railway domain
```

## Test Commands

Thay `YOUR_URL` và `YOUR_KEY` sau khi deploy:

```bash
curl https://YOUR_URL/health
curl https://YOUR_URL/ready

curl -X POST https://YOUR_URL/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello"}'
# Expected: 401

curl -X POST https://YOUR_URL/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello"}'
# Expected: 200
```

## Screenshots

| File | Mô tả |
|------|-------|
| [screenshots/docker-compose-running.png](screenshots/docker-compose-running.png) | Docker local |
| [screenshots/health-check.png](screenshots/health-check.png) | Health check |
| [screenshots/auth-test.png](screenshots/auth-test.png) | Auth test |
| [screenshots/rate-limit-test.png](screenshots/rate-limit-test.png) | Rate limit |
| [screenshots/production-ready-check.png](screenshots/production-ready-check.png) | 20/20 checks |
| [screenshots/cloud-dashboard.png](screenshots/cloud-dashboard.png) | Railway dashboard |

## Verified (Local)

```
check_production_ready.py: 20/20
Docker image: 307 MB
railway.toml: configured
```
