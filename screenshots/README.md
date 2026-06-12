# Screenshots for Day 12 Lab Submission

Place screenshots here before submitting:

1. **docker-compose-running.png** — output of `docker compose ps`
2. **health-check.png** — `curl http://localhost/health` response
3. **auth-test.png** — 401 without API key vs 200 with key
4. **cloud-dashboard.png** — Railway or Render deployment dashboard (optional for cloud deploy)

Generate locally after running:

```bash
cd 06-lab-complete
docker compose up --build -d
curl http://localhost/health
```
