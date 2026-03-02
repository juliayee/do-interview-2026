from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis
import os
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, text

from database import engine, SessionLocal, Score, init_db

# Initialize FastAPI app
app = FastAPI(title="Gaming Leaderboard API")

# Configure CORS for frontend communication
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
init_db()

# Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True) #stateless setup

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models
class ScoreSubmission(BaseModel):
    user_id: str
    score: float

class LeaderboardEntry(BaseModel):
    user_id: str
    score: float
    rank: int

class UserContext(BaseModel):
    user_rank: int
    user_score: float
    above: List[LeaderboardEntry]
    below: List[LeaderboardEntry]

# Helper function to get leaderboard key
def get_leaderboard_key(game_id: str) -> str:
    return f"leaderboard:{game_id}"

# Endpoints
# ZSCORE (get current): O(1) - direct key lookup
# ZADD (insert/update): O(log N) - Redis binary tree rebalancing
# ZREVRANGE (get top 10): O(log N + 10) - seek to position + fetch count

@app.get("/")
def root():
    """Root endpoint - API information and available routes"""
    return {
        "service": "Gaming Leaderboard API",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "http://localhost:8000/docs",
        "endpoints": {
            "health": {
                "path": "/health",
                "method": "GET",
                "description": "Health check - verifies PostgreSQL and Redis connectivity"
            },
            "submit_score": {
                "path": "/games/{game_id}/score",
                "method": "POST",
                "description": "Submit or update a user's score (keeps max)",
                "body": {"user_id": "string", "score": "float"}
            },
            "get_top_leaderboard": {
                "path": "/games/{game_id}/top",
                "method": "GET",
                "description": "Get top N players by score",
                "params": {"limit": "int (1-1000, default 10)"}
            },
            "get_user_context": {
                "path": "/games/{game_id}/user/{user_id}/context",
                "method": "GET",
                "description": "Get user's rank with nearby ranked players",
                "params": {"radius": "int (1-100, default 2)"}
            }
        },
        "databases": {
            "postgresql": "durable storage (source of truth)",
            "redis": "in-memory cache (fast rankings)"
        }
    }

@app.post("/games/{game_id}/score")
def submit_score(game_id: str, submission: ScoreSubmission, db: Session = Depends(get_db)):
    """Submit or update a user's score for a game (keeps max score)"""
    if not game_id or not submission.user_id:
        raise HTTPException(status_code=400, detail="game_id and user_id are required")
    if submission.score < 0:
        raise HTTPException(status_code=400, detail="Score must be non-negative")
    
    try:
        # 1. Write to PostgreSQL (durable, source of truth)
        composite_key = f"{game_id}:{submission.user_id}"
        
        # Check if user has existing score
        existing_score = db.query(Score).filter(
            and_(
                Score.game_id == game_id,
                Score.user_id == submission.user_id
            )
        ).first()
        
        # Only update if new score is higher (keep max)
        if existing_score is None:
            # New score
            new_score_record = Score(
                id=composite_key,
                game_id=game_id,
                user_id=submission.user_id,
                score=submission.score
            )
            db.add(new_score_record)
            db.commit()
            status = "updated"
        elif submission.score > existing_score.score:
            # Update if higher
            existing_score.score = submission.score
            db.commit()
            status = "updated"
        else:
            # Keep existing (higher) score
            db.rollback()
            return {"status": "unchanged", "game_id": game_id, "user_id": submission.user_id, "current_score": existing_score.score}
        
        # 2. Update Redis cache (for fast reads in this region)
        leaderboard_key = get_leaderboard_key(game_id)
        redis_client.zadd(leaderboard_key, {submission.user_id: submission.score})
        
        return {"status": status, "game_id": game_id, "user_id": submission.user_id, "score": submission.score, "persistent": True}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/games/{game_id}/top", response_model=List[LeaderboardEntry])
def get_top_leaderboard(game_id: str, limit: int = 10, db: Session = Depends(get_db)):
    """Get top N leaderboard entries for a game"""
    if not game_id:
        raise HTTPException(status_code=400, detail="game_id is required")
    if limit <= 0 or limit > 1000:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 1000")
    
    leaderboard_key = get_leaderboard_key(game_id)
    
    # Try Redis cache first (fast, <1ms)
    try:
        top_entries = redis_client.zrevrange(leaderboard_key, 0, limit - 1, withscores=True)
        if top_entries:
            result = []
            for rank, (user_id, score) in enumerate(top_entries, 1):
                result.append(LeaderboardEntry(user_id=user_id, score=float(score), rank=rank))
            return result
    except Exception as e:
        print(f"Redis cache miss or error: {e}")
    
    # Fall back to PostgreSQL (slower but always correct)
    try:
        scores = db.query(Score.user_id, Score.score).filter(
            Score.game_id == game_id
        ).order_by(desc(Score.score)).limit(limit).all()
        
        if not scores:
            return []
        
        result = []
        for rank, (user_id, score) in enumerate(scores, 1):
            result.append(LeaderboardEntry(user_id=user_id, score=float(score), rank=rank))
        
        # Warm up Redis cache with DB results
        for rank, (user_id, score) in enumerate(scores, 1):
            redis_client.zadd(leaderboard_key, {user_id: score})
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/games/{game_id}/user/{user_id}/context", response_model=UserContext)
def get_user_context(game_id: str, user_id: str, radius: int = 2, db: Session = Depends(get_db)):
    """Get user's rank with nearby leaderboard entries"""
    if not game_id or not user_id:
        raise HTTPException(status_code=400, detail="game_id and user_id are required")
    if radius <= 0 or radius > 100:
        raise HTTPException(status_code=400, detail="radius must be between 1 and 100")
    
    try:
        # Get user's score and rank from PostgreSQL
        user_score = db.query(Score.score).filter(
            and_(
                Score.game_id == game_id,
                Score.user_id == user_id
            )
        ).first()
        
        if not user_score:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found in game {game_id}")
        
        user_score = float(user_score[0])
        
        # Get user's rank
        rank_query = db.query(Score).filter(
            and_(
                Score.game_id == game_id,
                Score.score > user_score  # Count how many scores are higher
            )
        ).count()
        user_rank = rank_query + 1  # Convert to 1-based ranking
        
        # Get entries above user
        above_entries = db.query(Score.user_id, Score.score).filter(
            and_(
                Score.game_id == game_id,
                Score.score > user_score
            )
        ).order_by(desc(Score.score)).limit(radius).all()
        
        # Get entries below user
        below_entries = db.query(Score.user_id, Score.score).filter(
            and_(
                Score.game_id == game_id,
                Score.score < user_score
            )
        ).order_by(desc(Score.score)).limit(radius).all()
        
        above = []
        for i, (uid, score) in enumerate(above_entries):
            rank = user_rank - (len(above_entries) - i)
            above.append(LeaderboardEntry(user_id=uid, score=float(score), rank=rank))
        
        below = []
        for i, (uid, score) in enumerate(below_entries):
            rank = user_rank + i + 1
            below.append(LeaderboardEntry(user_id=uid, score=float(score), rank=rank))
        
        return UserContext(
            user_rank=user_rank,
            user_score=user_score,
            above=above,
            below=below
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/health")
def health_check():
    """Health check endpoint - verifies Redis and PostgreSQL"""
    status = {"status": "healthy", "components": {}}
    
    # Check Redis
    try:
        redis_client.ping()
        status["components"]["redis"] = "connected"
    except Exception as e:
        status["components"]["redis"] = f"error: {str(e)}"
        status["status"] = "degraded"
    
    # Check PostgreSQL
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        status["components"]["postgres"] = "connected"
    except Exception as e:
        status["components"]["postgres"] = f"error: {str(e)}"
        status["status"] = "unhealthy"
    
    # If PostgreSQL is down, service is unhealthy
    if status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=status)
    
    return status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
