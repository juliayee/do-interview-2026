# Gaming Leaderboard Service - Architecture Overview

## System Architecture Diagram

```mermaid
flowchart TD
  User[User / Frontend (Next.js)] -->|REST API| Backend[FastAPI]
  Backend -->|Leaderboard ops| Redis[(Sorted Sets)]
  Backend -->|Persistence| Postgres[(PostgreSQL)]
    C[Client (Browser/App)] <--> GW[API Gateway]
    GW <--> BE[Backend (FastAPI)]
    BE <--> R[Redis]
    BE <--> DB[PostgreSQL]
    C <--> F[Frontend (Next.js)]
    F <--> GW

    %% Descriptions
    C:::client
    F:::frontend
    GW:::gateway
    BE:::backend
    R:::redis
    DB:::db

    classDef client fill:#e3f2fd,stroke:#2196f3;
    classDef frontend fill:#f3e5f5,stroke:#8e24aa;
    classDef gateway fill:#fffde7,stroke:#fbc02d;
    classDef backend fill:#e8f5e9,stroke:#43a047;
    classDef redis fill:#ffebee,stroke:#d32f2f;
    classDef db fill:#ede7f6,stroke:#5e35b1;
  ```
  note right of Backend: All game/user IDs are case-insensitive and trimmed
```
    │   Backend API (FastAPI) - Port 8000               │
    │                                                    │
    │  POST   /games/{game_id}/score                    │
    │  ├─ Input: user_id, score                         │
    │  ├─ Logic: Keep max score per user                │
    │  └─ Store: Redis sorted set                       │
    │                                                    │
    │  GET    /games/{game_id}/top?limit=N              │
    │  ├─ Input: game_id, limit (1-1000)                │
    │  ├─ Logic: Fetch N highest scores (desc)          │
    │  └─ Return: Ranked list of users                  │
    │                                                    │
    │  GET    /games/{game_id}/user/{user_id}/context   │
    │  ├─ Input: user_id, radius (neighbors depth)      │
    │  ├─ Logic: User rank + nearby entries              │
    │  └─ Return: User's position with context          │
    │                                                    │
    │  GET    /health                                   │
    │  └─ Checks Redis connectivity                     │
    └────────────────┬─────────────────────────────────┘
                     │ Redis Protocol
                     ▼
         ┌──────────────────────────────┐
         │   Redis Sorted Sets          │
         │                              │
         │ leaderboard:game1            │
         │ leaderboard:game2            │
         │ leaderboard:gameN            │
         │                              │
         │ Data Structure:              │
         │ {                            │
         │   user1: 1500,               │
         │   user2: 2300,               │
         │   user3: 1200,               │
         │   ...                        │
         │ }                            │
         │                              │
         │ Features:                    │
         │ - O(log N) insert/update     │
         │ - O(1) range queries         │
         │ - In-memory performance      │
         │ - Persistent (AOF/RDB)       │
         └──────────────────────────────┘
```

## Request Flow Examples

### 1. Submit Score Flow
```
User Input (player1, score=2500) 
  ↓
Frontend Form → POST /games/game1/score
  ↓
FastAPI Endpoint
  ├─ Validate: user_id, score (>= 0)
  ├─ Get current max: ZSCORE leaderboard:game1 player1
  ├─ Compare: if new_score > current_score
  ├─ Update: ZADD leaderboard:game1 2500 player1
  └─ Return: {status: "updated", score: 2500}
  ↓
Frontend displays confirmation
```

### 2. Get Top Leaderboard Flow
```
User requests top 10
  ↓
Frontend GET /games/game1/top?limit=10
  ↓
FastAPI Endpoint
  ├─ Validate: limit (1-1000)
  ├─ Query: ZREVRANGE leaderboard:game1 0 9 WITHSCORES
  ├─ Map results with rank (1-10)
  └─ Return: [{rank: 1, user_id: "...", score: ...}, ...]
  ↓
Frontend renders table
```

### 3. Get User Context Flow
```
User searches for "player1"
  ↓
Frontend GET /games/game1/user/player1/context?radius=2
  ↓
FastAPI Endpoint
  ├─ Find rank: ZREVRANK leaderboard:game1 player1 → position
  ├─ Get score: ZSCORE leaderboard:game1 player1
  ├─ Fetch above: ZREVRANGE leaderboard:game1 (pos-3) (pos-2)
  ├─ Fetch below: ZREVRANGE leaderboard:game1 (pos+1) (pos+2)
  └─ Return: {user_rank, user_score, above: [...], below: [...]}
  ↓
Frontend renders user card with context
```

## Technology Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Backend API | FastAPI (Python) | Type-safe, auto-docs, high performance |
| Frontend | Next.js (TypeScript) | SSR, fast builds, excellent DX |
| Data Store | Redis Sorted Sets | O(log N) ops, real-time ranking, in-memory |
| Persistence | Redis AOF/RDB | Data durability without complexity |
| Containers | Docker | Consistent environments across dev/prod |
| Orchestration | docker-compose | Local development, DigitalOcean deployment |
| CI/CD | GitHub Actions | Free, integrated, fast feedback |

## Scalability Considerations

### Immediate (Deployed)
- API horizontal scaling: Multiple FastAPI replicas
- Load balancer: nginx reverse proxy
- Redis: Managed instance with replication

### Medium Term (100K+ users)
- Redis cluster for sharding by game_id
- API caching layer (Varnish/Memcached)
- Batch score submissions for batching

### Long Term (1M+ users)
- Event streaming (Kafka) for async processing
- Time-series DB for historical analytics
- Read replicas for leaderboard queries

## Error Handling & Validation

| Endpoint | Validations |
|----------|-------------|
| Submit Score | game_id required, user_id required, score >= 0 |
| Get Top | limit 1-1000, game_id required |
| User Context | user_id exists, radius 1-100, game_id required |

## Deployment on DigitalOcean

1. **App Platform**: Push docker-compose as app.yaml
2. **Managed Redis**: DigitalOcean Managed Database (non-production use local)
3. **Load Balancer**: DigitalOcean Load Balancer in front of API
4. **Monitoring**: DigitalOcean Monitoring + Datadog integration
5. **Backups**: Automated Redis snapshots

## Testing Strategy

- **Unit Tests**: FastAPI endpoints with TestClient
- **Integration Tests**: Full stack with docker-compose
- **Load Tests**: Apache JMeter for concurrent submissions
- **Health Checks**: Automated service monitoring

See [Backend README](backend/README.md) and [Frontend README](frontend/README.md) for implementation details.
