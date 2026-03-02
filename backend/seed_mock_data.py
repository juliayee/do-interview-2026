import random
from database import SessionLocal, Score, init_db

games = ["snake", "tetris", "atari"]
users = [f"user{i}" for i in range(1, 21)]

init_db()
db = SessionLocal()
for game in games:
    for user in users:
        score = random.randint(10, 10000)
        composite_key = f"{game}:{user}"
        db.merge(Score(id=composite_key, game_id=game, user_id=user, score=score))
db.commit()
db.close()
print("Mock data seeded for games: snake, tetris, atari.")
