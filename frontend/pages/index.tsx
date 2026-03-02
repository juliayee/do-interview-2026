import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface LeaderboardEntry {
  user_id: string;
  score: number;
  rank: number;
}

interface UserContext {
  user_rank: number;
  user_score: number;
  above: LeaderboardEntry[];
  below: LeaderboardEntry[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  const [gameId, setGameId] = useState('game1');
  const [userId, setUserId] = useState('');
  const [score, setScore] = useState('');
  const [topLeaderboard, setTopLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [userContext, setUserContext] = useState<UserContext | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [topLimit, setTopLimit] = useState(10);
  const [contextGameId, setContextGameId] = useState('game1');

  // Utility to normalize game name
  const normalizeGameName = (name: string) => name.trim().toLowerCase();

  // Utility to normalize user ID
  const normalizeUserId = (id: string) => id.trim().toLowerCase();

  const submitScore = async () => {
    if (!userId.trim()) {
      setError('User ID field is empty, please enter something');
      return;
    }
    if (!gameId.trim()) {
      setError('Game Name field is empty, please enter something');
      return;
    }
    if (!score.trim()) {
      setError('Score field is empty, please enter something');
      return;
    }
    try {
      setLoading(true);
      setError('');
      const response = await axios.post(`${API_BASE}/games/${normalizeGameName(gameId)}/score`, {
        user_id: normalizeUserId(userId),
        score: Number(score)
      });
      setScore('');
      await fetchTopLeaderboard();
      alert('Score submitted successfully!');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit score');
    } finally {
      setLoading(false);
    }
  };

  const fetchTopLeaderboard = async () => {
    try {
      const response = await axios.get(`${API_BASE}/games/${normalizeGameName(gameId)}/top?limit=${topLimit}`);
      setTopLeaderboard(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch leaderboard');
    }
  };

  const fetchUserContext = async () => {
    if (!userId.trim()) {
      setError('User ID field is empty, please enter something');
      return;
    }
    if (!contextGameId.trim()) {
      setError('Game Name field is empty, please enter something');
      return;
    }
    try {
      const response = await axios.get(`${API_BASE}/games/${normalizeGameName(contextGameId)}/user/${normalizeUserId(userId)}/context`);
      setUserContext(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch user context');
    }
  };

  // Remove useEffect for fetchTopLeaderboard

  return (
    <main className="discord-main">
      <h1 className="discord-title">🎮 Gaming Leaderboard</h1>
      <div className="discord-container">
        <section className="discord-card">
          <h2>Submit Score</h2>
          <form className="discord-form" onSubmit={e => { e.preventDefault(); submitScore(); }}>
            <label>
              <span>Game Name</span>
              <input className="discord-input" value={gameId} onChange={e => setGameId(e.target.value)} placeholder="e.g. snake, tetris, atari" />
            </label>
            <label>
              <span>User ID</span>
              <input className="discord-input" value={userId} onChange={e => setUserId(e.target.value)} />
            </label>
            <label>
              <span>Score</span>
              <input className="discord-input" type="number" value={score} onChange={e => setScore(e.target.value)} />
            </label>
            <button className="discord-btn" type="submit" disabled={loading}>Submit</button>
          </form>
        </section>
        <section className="discord-card">
          <h2>Top Scores</h2>
          <div className="discord-row">
            <label>
              <span>Game Name</span>
              <input className="discord-input" value={gameId} onChange={e => setGameId(e.target.value)} placeholder="e.g. snake, tetris, atari" />
            </label>
            <label>
              <span>Limit</span>
              <input className="discord-input" type="number" value={topLimit} min={1} max={100} onChange={e => setTopLimit(Number(e.target.value))} />
            </label>
            <button className="discord-btn" onClick={fetchTopLeaderboard}>Refresh</button>
          </div>
          <ol className="discord-list">
            {topLeaderboard.map(entry => (
              <li key={entry.user_id} className="discord-list-item">
                <span className="discord-rank">{entry.rank}.</span> <span className="discord-user">{entry.user_id}</span> <span className="discord-score">— {entry.score}</span>
              </li>
            ))}
          </ol>
        </section>
        <section className="discord-card">
          <h2>User Context</h2>
          <div className="discord-row">
            <label>
              <span>Game Name</span>
              <input className="discord-input" value={contextGameId} onChange={e => setContextGameId(e.target.value)} placeholder="e.g. snake, tetris, atari" />
            </label>
            <label>
              <span>User ID</span>
              <input className="discord-input" value={userId} onChange={e => setUserId(e.target.value)} />
            </label>
            <button className="discord-btn" onClick={fetchUserContext}>Get Context</button>
          </div>
          {userContext && (
            <div className="discord-context">
              <div><strong>User:</strong> <span className="discord-user">{userContext.user_rank}. {userId}</span> <span className="discord-score">— {userContext.user_score}</span></div>
              <div><strong>Above:</strong> {userContext.above && userContext.above.length > 0 ? <span className="discord-user">{userContext.above[0].user_id}</span> : 'None'} {userContext.above && userContext.above.length > 0 ? <span className="discord-score">({userContext.above[0].score})</span> : ''}</div>
              <div><strong>Below:</strong> {userContext.below && userContext.below.length > 0 ? <span className="discord-user">{userContext.below[0].user_id}</span> : 'None'} {userContext.below && userContext.below.length > 0 ? <span className="discord-score">({userContext.below[0].score})</span> : ''}</div>
            </div>
          )}
        </section>
        {error && <div className="discord-error">{error}</div>}
      </div>
    </main>
  );
}
