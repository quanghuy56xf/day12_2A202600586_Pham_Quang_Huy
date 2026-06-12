# Day 12 Lab — Mission Answers

> **Student:** HUY  
> **Course:** AICB-P1 · VinUniversity 2026  
> **Date:** 2026-06-12

---

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found

Đọc `01-localhost-vs-production/develop/app.py`, tìm được **8 vấn đề**:

1. **API key hardcode** — `OPENAI_API_KEY = "sk-hardcoded-fake-key..."` lộ secret khi push Git.
2. **Database credentials hardcode** — `DATABASE_URL` chứa username/password trong source code.
3. **Debug mode bật cố định** — `DEBUG = True` không đọc từ environment.
4. **Logging không an toàn** — dùng `print()` và log ra API key (`print(f"... {OPENAI_API_KEY}")`).
5. **Không có health check endpoint** — platform không biết khi nào restart container.
6. **Port cố định** — `port=8000` không đọc `PORT` env var (Railway/Render inject PORT).
7. **Bind localhost** — `host="localhost"` không nhận traffic từ bên ngoài container.
8. **Reload mode trong production** — `reload=True` không phù hợp khi deploy.

### Exercise 1.2: Chạy basic version

```bash
cd 01-localhost-vs-production/develop
pip install -r requirements.txt
python app.py
```

```bash
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```

**Quan sát:** App chạy được trên laptop nhưng **không production-ready** vì secrets hardcode, không health check, không graceful shutdown, bind localhost.

### Exercise 1.3: Comparison table

| Feature | Basic (develop) | Advanced (production) | Tại sao quan trọng? |
|---------|-----------------|----------------------|---------------------|
| Config | Hardcode trong code | Environment variables (`config.py`) | Secrets không lộ trên Git; config khác nhau theo môi trường |
| Health check | Không có | `GET /health` + `GET /ready` | Platform biết khi restart; LB biết khi route traffic |
| Logging | `print()` debug | Structured JSON logging | Dễ search/alert trong Datadog, CloudWatch |
| Shutdown | Đột ngột (kill process) | Graceful via lifespan + SIGTERM | Request đang xử lý không bị cắt giữa chừng |
| Host binding | `localhost` | `0.0.0.0` | Container/cloud nhận được external traffic |
| Port | Cố định 8000 | `PORT` env var | Cloud platforms inject port động |
| CORS | Không có | Middleware cấu hình origins | Kiểm soát client được phép gọi API |
| Input validation | Query param thô | Pydantic + HTTPException 422 | Tránh bad input, API contract rõ ràng |

### Checkpoint 1

- [x] Hiểu tại sao hardcode secrets là nguy hiểm
- [x] Biết cách dùng environment variables
- [x] Hiểu vai trò của health check endpoint
- [x] Biết graceful shutdown là gì

---

## Part 2: Docker

### Exercise 2.1: Dockerfile questions

1. **Base image:** `python:3.11` (full image ~1 GB)
2. **Working directory:** `/app`
3. **Tại sao COPY requirements.txt trước?** Docker layer caching — dependencies ít thay đổi hơn code, rebuild nhanh hơn khi chỉ sửa source.
4. **CMD vs ENTRYPOINT:** `CMD` là default command, có thể override khi `docker run`; `ENTRYPOINT` định nghĩa executable cố định, args từ `docker run` append vào.

### Exercise 2.2: Build và run (develop)

```bash
docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .
docker run -p 8000:8000 my-agent:develop
```

**Quan sát image size:** develop image ~1 GB+ (full `python:3.11` base).

### Exercise 2.3: Image size comparison

| Image | Base | Kích thước (ước lượng) |
|-------|------|------------------------|
| `my-agent:develop` | `python:3.11` (single-stage) | ~1.0–1.2 GB |
| `my-agent:advanced` | `python:3.11-slim` (multi-stage) | ~180–250 MB |
| `06-lab-complete` (final) | `python:3.11-slim` multi-stage | **307 MB** (verified) |

**Difference:** Production image nhỏ hơn ~75–80% nhờ slim base + multi-stage (builder tách khỏi runtime).

- **Stage 1 (builder):** Cài gcc, build deps, `pip install --user`
- **Stage 2 (runtime):** Chỉ copy site-packages + source, non-root user, HEALTHCHECK

### Exercise 2.4: Docker Compose stack

Architecture:

```
Client → Nginx (port 80) → Agent instances (round-robin)
                              ↓
                           Redis
```

Services: `agent`, `redis`, `nginx`. Agent không expose port trực tiếp; Nginx proxy tới `agent:8000` qua Docker DNS.

### Checkpoint 2

- [x] Hiểu cấu trúc Dockerfile
- [x] Biết lợi ích của multi-stage builds
- [x] Hiểu Docker Compose orchestration
- [x] Biết cách debug container (`docker logs`, `docker exec`)

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment

**Steps thực hiện:**

```bash
npm i -g @railway/cli
railway login
cd 06-lab-complete
railway init
railway variables set PORT=8000
railway variables set AGENT_API_KEY=<secret>
railway variables set REDIS_URL=<redis-url>
railway up
railway domain
```

**URL:** Xem `DEPLOYMENT.md` (local: `http://localhost` qua Docker Compose; cloud: deploy qua Railway/Render blueprint).

### Exercise 3.2: Render deployment

**So sánh `render.yaml` vs `railway.toml`:**

| Aspect | `railway.toml` | `render.yaml` |
|--------|----------------|---------------|
| Format | TOML, Railway-specific | YAML Blueprint, multi-service |
| Services | Single service implied | Web + Redis add-on explicit |
| Build | `builder = "DOCKERFILE"` | `runtime: docker` per service |
| Health check | `healthcheckPath` | `healthCheckPath` |
| Secrets | CLI/Dashboard | `sync: false`, `generateValue: true` |
| Redis | External/manual | Declared as `type: redis` service |

### Exercise 3.3: GCP Cloud Run (Optional)

- `cloudbuild.yaml`: CI pipeline build image → push Artifact Registry → deploy Cloud Run
- `service.yaml`: Knative service spec — concurrency, memory, env vars, traffic routing

### Checkpoint 3

- [x] Deploy thành công lên ít nhất 1 platform (Docker local + config sẵn sàng Railway/Render)
- [x] Public/local URL hoạt động
- [x] Hiểu cách set environment variables trên cloud
- [x] Biết cách xem logs (`docker compose logs`, Railway/Render dashboard)

---

## Part 4: API Security

### Exercise 4.1: API Key authentication

- **Check ở đâu:** Dependency `verify_api_key()` trong `app/auth.py`, inject qua `Depends(verify_api_key)`.
- **Sai key:** HTTP **401** — `"Invalid or missing API key"`.
- **Rotate key:** Set env var `AGENT_API_KEY` mới trên platform, restart service. Không cần đổi code.

### Exercise 4.1-4.3: Test results (verified)

```
Health: HTTP 200 {"status":"ok",...}
Ready:  HTTP 200 {"ready":true,"redis":"connected"}
No API key: HTTP 401
With API key: HTTP 200
Rate limit: HTTP 200 x10, then HTTP 429 (requests 11-12)
Conversation history: history_length 2 → 4 across turns
```

### Exercise 4.2: JWT authentication (Advanced)

Flow trong `04-api-gateway/production/`:

1. `POST /token` với username/password → nhận JWT
2. Gọi API với `Authorization: Bearer <token>`
3. Server verify signature + expiry qua `auth.py`

Admin bypass rate limit: role `admin` dùng `rate_limiter_admin` (100 req/min) thay vì user limit (10 req/min).

### Exercise 4.3: Rate limiting

- **Algorithm:** Sliding window (Redis sorted set trong final project; in-memory deque trong demo)
- **Limit:** **10 requests/minute** per user
- **Admin bypass:** JWT role `admin` → bucket riêng với limit cao hơn

Khi hit limit → HTTP **429** + header `Retry-After: 60`.

### Exercise 4.4: Cost guard implementation

**Approach (Redis, monthly per user):**

```python
def check_budget(user_id: str, estimated_cost: float) -> None:
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"
    current = float(redis.get(key) or 0)
    if current + estimated_cost > settings.monthly_budget_usd:  # $10/month
        raise HTTPException(402, ...)
    redis.incrbyfloat(key, estimated_cost)
    redis.expire(key, 32 * 24 * 3600)
```

Implemented in `06-lab-complete/app/cost_guard.py`.

### Checkpoint 4

- [x] Implement API key authentication
- [x] Hiểu JWT flow
- [x] Implement rate limiting (10 req/min)
- [x] Implement cost guard với Redis ($10/month)

---

## Part 5: Scaling & Reliability

### Exercise 5.1: Health checks

```python
@app.get("/health")
def health():
    return {"status": "ok", ...}  # Liveness — process alive

@app.get("/ready")
def ready():
    if not _is_ready or not ping_redis():
        raise HTTPException(503, "Not ready")
    return {"ready": True}  # Readiness — deps OK
```

### Exercise 5.2: Graceful shutdown

- FastAPI `lifespan` context manager: set `_is_ready = False` on shutdown
- `signal.signal(SIGTERM, handler)` log signal
- `uvicorn` với `timeout_graceful_shutdown=30` hoàn thành in-flight requests

### Exercise 5.3: Stateless design

**Anti-pattern:** `conversation_history = {}` in memory  
**Correct:** Redis keys `history:{user_id}` — mọi agent instance đọc cùng state

Implemented in `06-lab-complete/app/session.py`.

### Exercise 5.4: Load balancing

```bash
cd 06-lab-complete
docker compose up --scale agent=3
```

Nginx upstream `agent:8000` round-robin qua Docker DNS. Header `X-Served-By` cho thấy instance xử lý request.

### Exercise 5.5: Test stateless

Conversation history persist qua Redis — kill một agent instance, request tiếp theo vẫn có history vì state không nằm trong memory của instance.

### Checkpoint 5

- [x] Implement health và readiness checks
- [x] Implement graceful shutdown
- [x] Refactor code thành stateless (Redis)
- [x] Hiểu load balancing với Nginx
- [x] Test stateless design

---

## Part 6: Final Project Summary

Full implementation: `06-lab-complete/`

| Requirement | Status |
|-------------|--------|
| REST API `/ask` | ✅ |
| Conversation history (Redis) | ✅ |
| Multi-stage Dockerfile (< 500 MB) | ✅ |
| Env-based config | ✅ |
| API key auth | ✅ |
| Rate limit 10 req/min | ✅ |
| Cost guard $10/month | ✅ |
| `/health` + `/ready` | ✅ |
| Graceful shutdown | ✅ |
| Stateless (Redis) | ✅ |
| JSON logging | ✅ |
| Docker Compose + Nginx | ✅ |
| Railway/Render config | ✅ |

Validation: `python check_production_ready.py` (see DEPLOYMENT.md for live test output).
