# Deployment Information

## Public URL (Railway)

**Production URL:** https://ai-agent-production-production-0abb.up.railway.app

| Item | Value |
|------|-------|
| Platform | Railway |
| Project | Day12-AI-Agent |
| Service | ai-agent-production |
| Redis | Redis (plugin) |

## Environment Variables (Railway)

| Variable | Value |
|----------|-------|
| `ENVIRONMENT` | `production` |
| `AGENT_API_KEY` | set on Railway Dashboard |
| `JWT_SECRET` | set on Railway Dashboard |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` |
| `RATE_LIMIT_PER_MINUTE` | `10` |
| `MONTHLY_BUDGET_USD` | `10.0` |

## Test Commands

### Health Check

```bash
curl https://ai-agent-production-production-0abb.up.railway.app/health
# Expected: {"status":"ok",...}
```

### Readiness Check

```bash
curl https://ai-agent-production-production-0abb.up.railway.app/ready
# Expected: {"ready":true,"redis":"connected"}
```

### Authentication required (401)

```bash
curl -X POST https://ai-agent-production-production-0abb.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello"}'
```

### API Test (with authentication)

```bash
curl -X POST https://ai-agent-production-production-0abb.up.railway.app/ask \
  -H "X-API-Key: YOUR_RAILWAY_AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello"}'
```

> Lấy `AGENT_API_KEY` từ Railway Dashboard → service **ai-agent-production** → Variables.

## Verified (Railway — 2026-06-12)

```
GET /health  → HTTP 200
GET /ready   → HTTP 200 (redis connected)
POST /ask    → HTTP 401 (no key)
POST /ask    → HTTP 200 (with X-API-Key)
```

## Railway Dashboard

https://railway.com/project/9ea5b4b4-dc09-476f-b18e-e2bdc64d0800

## Screenshots

| File | Mô tả |
|------|-------|
| [screenshots/docker-compose-running.png](screenshots/docker-compose-running.png) | Docker local |
| [screenshots/health-check.png](screenshots/health-check.png) | Health check |
| [screenshots/auth-test.png](screenshots/auth-test.png) | Auth test |
| [screenshots/rate-limit-test.png](screenshots/rate-limit-test.png) | Rate limit |
| [screenshots/production-ready-check.png](screenshots/production-ready-check.png) | 20/20 checks |
| [screenshots/cloud-dashboard.png](screenshots/cloud-dashboard.png) | Railway dashboard |
| [screenshots/railway-live-test.png](screenshots/railway-live-test.png) | Railway live API tests |

## Pre-Submission Checklist

- [x] Repository public: https://github.com/quanghuy56xf/day12_2A202600586_Pham_Quang_Huy
- [x] `MISSION_ANSWERS.md` completed
- [x] `DEPLOYMENT.md` has working public URL
- [x] Source code in `06-lab-complete/app/`
- [x] `README.md` setup instructions
- [x] No `.env` committed (only `.env.example`)
- [x] No hardcoded secrets in code
- [x] Public URL accessible and working
- [x] Screenshots in `screenshots/`
- [x] Clear commit history

## Redeploy

```bash
cd 06-lab-complete
railway up -y -d
```
