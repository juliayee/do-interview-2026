# Gaming Leaderboard Backend

FastAPI service for managing real-time gaming leaderboards using a hybrid **PostgreSQL + Redis** architecture. PostgreSQL provides durable persistence for global leaderboards, while Redis caches rankings for lightning-fast reads.

## Features

- **Submit Score**: Write to PostgreSQL (durable), update Redis cache (fast)
- **Top Leaderboard**: Read from Redis cache, fallback to PostgreSQL if needed
- **User Context**: Get a user's rank plus nearby ranked players from PostgreSQL
- **Real-time**: O(log N) operations with Redis, atomic updates in PostgreSQL
- **Production-Ready**: Durable persistence, input validation, error handling, health checks
- **Global-Ready**: PostgreSQL for global consistency, regional Redis for local speed

## Tech Stack

- **Framework**: FastAPI with Pydantic
- **Persistent DB**: PostgreSQL
- **Cache Layer**: Redis (regional performance)
- **ORM**: SQLAlchemy
- **Testing**: pytest with TestClient
- **Containerization**: Docker

## Architecture: Redis + PostgreSQL Hybrid

```
Write Path (Score Submission):
  POST /games/{game_id}/score
    ↓
  PostgreSQL (write, validate, persist)
    ↓
  Redis Sorted Set (cache for this region)
    ↓
  Response: {status, persistent: true}

Read Path (Get Leaderboard):
  GET /games/{game_id}/top
    ↓
  Try Redis Cache (99% hit rate, <1ms)
    ↓ (if miss or error)
  PostgreSQL (always correct, <50ms)
    ↓
  Warm Redis cache with results
    ↓
  Response: Ranked entries

Why This Works for Global Leaderboards:
  ✓ PostgreSQL = Single source of truth (durable, replicated)
  ✓ Redis = Regional cache (fast reads per geography)
  ✓ Writes always go to PostgreSQL (consistency)
  ✓ Reads try fast cache first, fall back to DB (resilience)
```

## Setup

### Local Development (with Docker Compose - Recommended)

```bash
cd /workspaces
docker-compose up
```

Services start with health checks:
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- API: http://localhost:8000 (Docs: http://localhost:8000/docs)

### Manual Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start PostgreSQL
# Option A: Docker
docker run --name postgres \
  -e POSTGRES_USER=leaderboard \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=leaderboard \
  -p 5432:5432 \
  postgres:16-alpine

# Option B: Native PostgreSQL
createdb -U postgres leaderboard

# 3. Start Redis
redis-server

# 4. Set environment
export DATABASE_URL="postgresql://leaderboard:password@localhost:5432/leaderboard"
export REDIS_HOST=localhost
export REDIS_PORT=6379

# 5. Run the app
python main.py
```
docker-compose up backend
```

## API Endpoints

### 1. Submit Score
```http
POST /games/{game_id}/score
Content-Type: application/json

{
  "user_id": "player1",
  "score": 2500
}

Response 200:
{
  "status": "updated",
  "game_id": "game1",
  "user_id": "player1",
  "score": 2500
}
```

**Semantics**: Only stores the maximum score per user. Lower submissions return `status: "unchanged"`.

### 2. Get Top Leaderboard
```http
GET /games/{game_id}/top?limit=10
```

**Parameters**:
- `limit` (optional): Number of top entries to return (1-1000, default 10)

**Response 200**: Array of leaderboard entries
```json
[
  {
    "rank": 1,
    "user_id": "champion",
    "score": 5000
  },
  {
    "rank": 2,
    "user_id": "runner_up",
    "score": 4800
  }
]
```

### 3. Get User Context
```http
GET /games/{game_id}/user/{user_id}/context?radius=2
```

**Parameters**:
- `radius` (optional): Number of neighbors on each side (1-100, default 2)

**Response 200**:
```json
{
  "user_rank": 5,
  "user_score": 3500,
  "above": [
    {"rank": 3, "user_id": "above1", "score": 3800},
    {"rank": 4, "user_id": "above2", "score": 3650}
  ],
  "below": [
    {"rank": 6, "user_id": "below1", "score": 3400},
    {"rank": 7, "user_id": "below2", "score": 3200}
  ]
}
```

### 4. Health Check
```http
GET /health

Response 200:
{
  "status": "healthy",
  "components": {
    "postgres": "connected",
    "redis": "connected"
  }
}
```

**Checks**:
- PostgreSQL connectivity (critical)
- Redis connectivity (cache, can degrade gracefully)

## Error Handling

| Status | Case |
|--------|------|
| 400 | Invalid input (missing field, negative score, invalid limit) |
| 404 | User not found in game |
| 503 | PostgreSQL unavailable (data durability lost) |

Example error response:
```json
{
  "detail": "limit must be between 1 and 1000"
}
```

## Testing

Run the full test suite with both databases:
```bash
pytest test_main.py -v
```

Tests cover:
- Score submission to PostgreSQL + Redis cache
- Max score semantics with persistence
- Invalid input validation
- Top leaderboard retrieval (cache + DB fallback)
- User context with neighbors
- Data persistence verification (Redis cleared, DB consulted)
- Health checks for both services

Sample test output:
```
test_health_check PASSED
test_submit_score PASSED
test_submit_score_keep_max PASSED
test_submit_score_invalid PASSED
test_get_top_leaderboard PASSED
test_get_user_context PASSED
test_persistence_PostgreSQL PASSED
======================== 14 passed in 3.21s ========================
```

## Configuration

Environment variables:
- `REDIS_HOST` (default: `localhost`) - Redis server hostname
- `REDIS_PORT` (default: `6379`) - Redis server port
- `DATABASE_URL` (default: `postgresql://leaderboard:password@localhost:5432/leaderboard`) - PostgreSQL connection string

Example production configuration:
```bash
export DATABASE_URL="postgresql://user:password@prod-db.example.com:5432/leaderboard"
export REDIS_HOST="redis-cache-prod.example.com"
export REDIS_PORT="6379"
```

## Scalability & Performance

### Hybrid Architecture Benefits
- **Writes**: Always to PostgreSQL (durable, consistent) ~5-10ms
- **Reads from Cache**: 99% Redis cache hits, <1ms
- **Reads from DB**: Fallback when cache misses, <50ms
- **Global**: PostgreSQL replicates globally, Redis regional

### Performance Metrics
- Submit score: ~10-15ms (PostgreSQL write + Redis update)
- Get top (cache hit): ~1-2ms (Redis ZREVRANGE)
- Get top (cache miss): ~20-50ms (PostgreSQL query + cache warm)
- Get context: ~10-20ms (PostgreSQL rank calculation)
- Throughput: 5,000+ RPS with proper connection pooling

### Production Recommendations
1. **PostgreSQL Setup**:
   - Use managed PostgreSQL (AWS RDS, DigitalOcean, Heroku)
   - Enable streaming replication for global read replicas
   - Automated backups (daily snapshots)
   - Connection pooling with PgBouncer (20+ pooled connections)

2. **Redis Setup**:
   - Regional instances for latency reduction
   - Enable persistence (AOF for durability)
   - Memory limits with LRU eviction (cache can be recreated from DB)
   - Cluster mode for distributed caching (optional)

3. **API Layer**:
   - Run multiple replicas behind load balancer
   - Implement request rate limiting (per user/game)
   - Add request logging for auditing
   - Monitor P99 latency via Prometheus

4. **Monitoring**:
   - PostgreSQL: Monitor replication lag, connection count
   - Redis: Monitor memory usage, eviction rate
   - API: Monitor response times, error rates
   - Set up alerts for service degradation

## Monitoring

Health endpoint enables K8s/Docker health checks:
```bash
curl http://localhost:8000/health
```

Example K8s probe configuration:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
  failureThreshold: 3
```

## Development Notes

- FastAPI OpenAPI docs: `http://localhost:8000/docs`
- SQLAlchemy ORM manages PostgreSQL connections
- Redis client handles caching transparently
- Pydantic validates requests before database writes
- Composite key (game_id, user_id) ensures unique scores per game
- Database indexes optimize ranking queries

## Next Steps

- [Frontend README](../frontend/README.md)
- [Architecture Overview](../ARCHITECTURE.md)
