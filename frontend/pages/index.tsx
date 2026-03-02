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

  const submitScore = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await axios.post(`${API_BASE}/games/${gameId}/score`, {
        user_id: userId,
        score: parseFloat(score)
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
      const response = await axios.get(`${API_BASE}/games/${gameId}/top?limit=10`);
      setTopLeaderboard(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch leaderboard');
    }
  };

  const fetchUserContext = async () => {
    try {
      const response = await axios.get(`${API_BASE}/games/${gameId}/user/${userId}/context?radius=2`);
      setUserContext(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch user context');
    }
  };

  useEffect(() => {
    fetchTopLeaderboard();
  }, [gameId]);

  return (
    <div style={styles.container}>
      <h1>Gaming Leaderboard</h1>
      
      <div style={styles.section}>
        <h2>Submit Score</h2>
        <div style={styles.form}>
          <input
            type="text"
            placeholder="Game ID"
            value={gameId}
            onChange={(e) => setGameId(e.target.value)}
            style={styles.input}
          />
          <input
            type="text"
            placeholder="User ID"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            style={styles.input}
          />
          <input
            type="number"
            placeholder="Score"
            value={score}
            onChange={(e) => setScore(e.target.value)}
            style={styles.input}
          />
          <button onClick={submitScore} disabled={loading} style={styles.button}>
            {loading ? 'Submitting...' : 'Submit'}
          </button>
        </div>
      </div>

      {error && <div style={styles.error}>{error}</div>}

      <div style={styles.section}>
        <h2>Top 10 Leaderboard</h2>
        {topLeaderboard.length > 0 ? (
          <table style={styles.table}>
            <thead>
              <tr>
                <th>Rank</th>
                <th>User ID</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              {topLeaderboard.map((entry) => (
                <tr key={entry.user_id}>
                  <td>{entry.rank}</td>
                  <td>{entry.user_id}</td>
                  <td>{entry.score}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No entries yet</p>
        )}
      </div>

      <div style={styles.section}>
        <h2>User Context</h2>
        <div style={styles.form}>
          <input
            type="text"
            placeholder="User ID to check"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            style={styles.input}
          />
          <button onClick={fetchUserContext} style={styles.button}>
            Get Context
          </button>
        </div>
        {userContext && (
          <div style={styles.context}>
            <p><strong>User Rank:</strong> {userContext.user_rank}</p>
            <p><strong>User Score:</strong> {userContext.user_score}</p>
            <h3>Above</h3>
            {userContext.above.length > 0 ? (
              <ul>
                {userContext.above.map((entry) => (
                  <li key={entry.user_id}>#{entry.rank} {entry.user_id}: {entry.score}</li>
                ))}
              </ul>
            ) : (
              <p>No entries above</p>
            )}
            <h3>Below</h3>
            {userContext.below.length > 0 ? (
              <ul>
                {userContext.below.map((entry) => (
                  <li key={entry.user_id}>#{entry.rank} {entry.user_id}: {entry.score}</li>
                ))}
              </ul>
            ) : (
              <p>No entries below</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '20px',
    fontFamily: 'Arial, sans-serif',
  } as React.CSSProperties,
  section: {
    marginBottom: '30px',
    border: '1px solid #ddd',
    padding: '15px',
    borderRadius: '8px',
  } as React.CSSProperties,
  form: {
    display: 'flex',
    gap: '10px',
    marginBottom: '10px',
    flexWrap: 'wrap',
  } as React.CSSProperties,
  input: {
    padding: '8px 12px',
    border: '1px solid #ccc',
    borderRadius: '4px',
    fontSize: '14px',
  } as React.CSSProperties,
  button: {
    padding: '8px 20px',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  } as React.CSSProperties,
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  } as React.CSSProperties,
  error: {
    color: '#d32f2f',
    padding: '10px',
    backgroundColor: '#ffebee',
    borderRadius: '4px',
    marginBottom: '10px',
  } as React.CSSProperties,
  context: {
    marginTop: '15px',
    padding: '10px',
    backgroundColor: '#f5f5f5',
    borderRadius: '4px',
  } as React.CSSProperties,
};
