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

## Redeploy

```bash
cd 06-lab-complete
railway up -y -d
```
