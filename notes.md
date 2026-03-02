# Design Notes & Architectural Trade-offs

## Key Design Choices

- **FastAPI Backend**: Chosen for speed, async support, and automatic OpenAPI docs. Enables rapid development and robust validation.
- **PostgreSQL for Persistence**: Ensures durability, ACID compliance, and global consistency for scores. Scales well for large datasets.
- **Redis for Leaderboard Caching**: Uses sorted sets for fast top-N queries and real-time rank lookups. Reduces database load and latency.
- **Next.js Frontend**: React-based, supports SSR/SSG for performance and SEO. Discord-style UI for familiar gamer experience.
- **Input Normalization**: All game/user IDs are lowercased and trimmed to prevent duplicates and ensure consistent lookups.
- **Error Handling & Validation**: Strict payload validation and clear error messages for reliability and security.
- **Docker Compose**: Simplifies local development and deployment, ensuring consistent environments across dev, CI, and production.
- **API Gateway (optional)**: Can be added for rate limiting, auth, and routing in production.
- **CI Pipeline**: Automated tests and linting for code quality and reliability.

## Architectural Trade-offs & Prioritizations

- **Performance vs. Consistency**: Redis is used for fast leaderboard reads, but PostgreSQL is the source of truth for durability. This hybrid approach prioritizes speed for common queries while ensuring data integrity.
- **Simplicity vs. Extensibility**: The system is modular (separate backend, frontend, cache, DB) for easy scaling and maintenance, but skips microservices for simplicity at this stage.
- **Skipped Features**:
  - No authentication/authorization (can be added via API Gateway or backend middleware)
  - No rate limiting (API Gateway or Redis can be used)
  - No multi-region DB replication (PostgreSQL can be extended with read replicas)
  - No advanced analytics (can be added with separate service)
  - No real-time push (WebSockets or polling can be added)

## Scaling the Service

- **Backend**: Deploy multiple FastAPI instances behind a load balancer (e.g., NGINX, API Gateway).
- **Database**: Use PostgreSQL read replicas for scaling reads; partition tables for very large datasets.
- **Cache**: Redis can be clustered for high availability and throughput.
- **Frontend**: Deploy on Vercel, Netlify, or similar for global CDN and scaling.
- **API Gateway**: Add for routing, rate limiting, and security as traffic grows.
- **Monitoring & Logging**: Integrate with Prometheus, Grafana, ELK stack for observability.
- **CI/CD**: Automate deployments and tests for reliability.

---

This file summarizes the rationale behind design choices, trade-offs made for production-readiness, and outlines how to scale the system as usage grows.