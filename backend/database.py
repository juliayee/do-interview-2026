import os
from sqlalchemy import create_engine, Column, String, Float, DateTime, Index, UniqueConstraint, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Database connection string
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://leaderboard:password@localhost:5432/leaderboard"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True  # Verify connections before using
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Score(Base):
    """Score model for PostgreSQL persistence"""
    __tablename__ = "scores"

    id = Column(String, primary_key=True)  # Composite key as string for simplicity
    game_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint: one score per user per game (composite key)
    __table_args__ = (
        UniqueConstraint('game_id', 'user_id', name='uq_game_user'),
        Index('idx_game_score', 'game_id', 'score'),  # Simple index for ranking queries
    )

    def __repr__(self):
        return f"<Score(game_id={self.game_id}, user_id={self.user_id}, score={self.score})>"


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
