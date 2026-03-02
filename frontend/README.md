# Gaming Leaderboard Frontend

Next.js TypeScript UI for the Gaming Leaderboard API. Submit scores, view rankings, and check user context.

## Features

- **Score Submission**: Simple form to submit user scores
- **Top Leaderboard**: Real-time display of top 10 players with ranks
- **User Context**: Search any user and see their rank with surrounding players
- **Multi-Game Support**: Switch between different games
- **Responsive Design**: Works on desktop and mobile

## Tech Stack

- **Framework**: Next.js 14 with TypeScript
- **HTTP Client**: Axios for API calls
- **Styling**: Inline CSS (can be extended with Tailwind)
- **Testing**: Jest + React Testing Library ready

## Setup

### Local Development

```bash
# Install dependencies
npm install

# Development server
npm run dev
# Frontend runs on http://localhost:3000
```

### With Docker Compose (from root)

```bash
docker-compose up frontend
# or full stack:
docker-compose up
```

### Environment Variables

Create a `.env.local` file:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For production:
```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

## Architecture

```
Pages/Components:
├── pages/
│   ├── _app.tsx           # App wrapper
│   ├── index.tsx          # Main page with all features
│   └── api/               # Optional: BFF endpoints
├── styles/                # Can organize styles here
└── components/            # Reusable components (future)
```

## Usage Guide

### 1. Submit a Score

1. **Enter Game ID** (default: "game1")
2. **Enter User ID** (e.g., "player1")
3. **Enter Score** (any non-negative number)
4. Click **Submit**
5. Score updates immediately in top leaderboard if ranked

### 2. View Top Leaderboard

- **Automatic**: Displays top 10 when page loads or game ID changes
- **Shows**: Rank, User ID, Score
- **Updates**: After each score submission

### 3. Check User Context

1. **Enter User ID** to search
2. Click **Get Context**
3. **See**:
   - User's current rank
   - User's score
   - Players ranked above (neighbors)
   - Players ranked below (neighbors)

## Component Structure

### Main Component: `pages/index.tsx`

**State Management**:
```typescript
- gameId: Current game (default: "game1")
- userId: User searching for
- score: Score to submit
- topLeaderboard: Array of top entries
- userContext: User rank with neighbors
- error: Error messages
- loading: Submission state
```

**Event Handlers**:
- `submitScore()`: POST score, refresh leaderboard
- `fetchTopLeaderboard()`: Fetch top 10
- `fetchUserContext()`: Fetch user's rank + context

**Rendering**:
- Score submission form
- Top leaderboard table
- User context details

## API Integration

All calls use the public API base URL:

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

**Endpoints Used**:
- `POST /games/{gameId}/score` - Submit
- `GET /games/{gameId}/top?limit=10` - Rankings
- `GET /games/{gameId}/user/{userId}/context?radius=2` - User info

**Error Handling**:
- Catches API errors and displays user-friendly messages
- Validates form inputs before submission
- Shows loading state during requests

## Styling

Inline CSS objects for demo purposes. For production:

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

Then convert to Tailwind classes.

## Building & Deployment

```bash
# Build production bundle
npm run build

# Start production server
npm start

# Export static site (if no API calls needed)
npm run export
```

### Docker Build
```bash
docker build -t leaderboard-frontend:latest .
```

### Deployment Platforms

**DigitalOcean App Platform**:
```yaml
name: leaderboard-frontend
services:
  - name: frontend
    github:
      repo: yourusername/leaderboard
      branch: main
    build_command: npm install && npm run build
    run_command: npm start
    envs:
      - key: NEXT_PUBLIC_API_URL
        value: https://api.yourdomain.com
```

**Vercel** (Recommended for Next.js):
1. Push repo to GitHub
2. Connect repo in Vercel dashboard
3. Set `NEXT_PUBLIC_API_URL` in environment
4. Deploy automatically on push

**Self-Hosted Docker**:
```bash
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://api.example.com \
  leaderboard-frontend:latest
```

## Testing

```bash
npm run test
```

Example test:
```typescript
import { render, screen } from '@testing-library/react';
import Home from '../pages/index';

test('renders submit score button', () => {
  render(<Home />);
  expect(screen.getByText('Submit')).toBeInTheDocument();
});
```

## Development Notes

- **CORS**: Backend must allow frontend origin
  - Local: `http://localhost:3000`
  - Prod: `https://yourdomain.com`
- **API Response Format**: Follows backend Pydantic models
- **Type Safety**: All API responses typed with interfaces
- **Performance**: Uses `useEffect` for data fetching

## Future Enhancements

- [ ] Pagination for leaderboard
- [ ] Real-time updates with WebSockets
- [ ] User authentication
- [ ] Leaderboard filters (time windows)
- [ ] Score history/trends chart
- [ ] Export leaderboard as CSV
- [ ] Mobile app with React Native

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Failed to fetch" | Check API_URL env var, ensure backend is running |
| CORS errors | Add frontend URL to backend CORS config |
| Blank page | Check browser console for errors, ensure Node 18+ |
| Slow on startup | First build takes longer, use `npm run build` then `npm start` |

## Next Steps

- [Backend README](../backend/README.md)
- [Architecture Overview](../ARCHITECTURE.md)
