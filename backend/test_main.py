import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, redis_client, get_leaderboard_key
from database import Base, Score, SessionLocal
import os

# Use SQLite for tests (in-memory)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine_test = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

# Override database dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Apply overrides
from main import SessionLocal
app.dependency_overrides[SessionLocal] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function", autouse=True)
def setup_teardown():
    """Setup test database and clean up after each test"""
    # Create test tables
    Base.metadata.create_all(bind=engine_test)
    
    yield
    
    # Clean up
    Base.metadata.drop_all(bind=engine_test)
    
    # Clean Redis
    keys = redis_client.keys("leaderboard:*")
    if keys:
        redis_client.delete(*keys)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in ["healthy", "degraded"]
    assert "components" in response.json()

def test_submit_score():
    """Test score submission to both Redis and PostgreSQL"""
    response = client.post("/games/game1/score", json={"user_id": "player1", "score": 100})
    assert response.status_code == 200
    assert response.json()["status"] == "updated"
    assert response.json()["score"] == 100
    assert response.json()["persistent"] == True

def test_submit_score_keep_max():
    """Test that only max score is kept in both DBs"""
    client.post("/games/game1/score", json={"user_id": "player1", "score": 100})
    response = client.post("/games/game1/score", json={"user_id": "player1", "score": 50})
    assert response.status_code == 200
    assert response.json()["status"] == "unchanged"

def test_submit_score_invalid():
    """Test invalid score submission"""
    response = client.post("/games/game1/score", json={"user_id": "player1", "score": -10})
    assert response.status_code == 400

def test_get_top_leaderboard():
    """Test getting top leaderboard (Redis cache with PostgreSQL fallback)"""
    # Submit scores
    scores = [("player1", 100), ("player2", 200), ("player3", 150), ("player4", 250)]
    for user_id, score in scores:
        client.post("/games/game1/score", json={"user_id": user_id, "score": score})
    
    # Get top 2 from Redis cache
    response = client.get("/games/game1/top?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["user_id"] == "player4"
    assert data[0]["score"] == 250
    assert data[0]["rank"] == 1
    assert data[1]["user_id"] == "player2"
    assert data[1]["rank"] == 2

def test_get_top_leaderboard_invalid_limit():
    """Test invalid limit parameter"""
    response = client.get("/games/game1/top?limit=2000")
    assert response.status_code == 400

def test_get_user_context():
    """Test getting user context"""
    # Submit scores
    scores = [("p1", 100), ("p2", 200), ("p3", 150), ("p4", 250), ("p5", 300)]
    for user_id, score in scores:
        client.post("/games/game1/score", json={"user_id": user_id, "score": score})
    
    # Get context for p2 (rank 4)
    response = client.get("/games/game1/user/p2/context?radius=1")
    assert response.status_code == 200
    data = response.json()
    assert data["user_rank"] == 2
    assert data["user_score"] == 200

def test_get_user_context_not_found():
    """Test user context for non-existent user"""
    response = client.get("/games/game1/user/nonexistent/context")
    assert response.status_code == 404

def test_persistence_PostgreSQL():
    """Test that data persists in PostgreSQL"""
    # Submit score
    client.post("/games/game1/score", json={"user_id": "persistent_user", "score": 500})
    
    # Clear Redis cache
    redis_client.delete("leaderboard:game1")
    
    # Query should still work from PostgreSQL
    response = client.get("/games/game1/top?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["user_id"] == "persistent_user"
    assert data[0]["score"] == 500


