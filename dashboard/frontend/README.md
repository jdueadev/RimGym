# RimWorld ML Dashboard Frontend

React + TypeScript frontend for the RimWorld ML training dashboard.

## Tech Stack

- **React 18**: UI framework
- **TypeScript**: Type safety
- **TanStack Query**: Data fetching and caching
- **Plotly.js**: Interactive charts
- **Tailwind CSS**: Styling

## Quick Start

### Development

```bash
cd dashboard/frontend
npm install
npm start
```

The app will open at `http://localhost:3000`.

### Production Build

```bash
npm run build
```

### Docker

```bash
docker build -t rimworld-ml-dashboard-frontend .
docker run -p 3000:3000 rimworld-ml-dashboard-frontend
```

## Environment Variables

Create `.env` file:

```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

## Project Structure

```
dashboard/frontend/
├── public/
│   └── index.html
├── src/
│   ├── index.tsx         # Entry point
│   ├── App.tsx           # Main app component
│   ├── index.css         # Global styles (Tailwind)
│   ├── components/       # React components
│   │   ├── Dashboard.tsx
│   │   ├── RunSelector.tsx
│   │   ├── ColonistList.tsx
│   │   ├── ResourcePanel.tsx
│   │   ├── ThreatMonitor.tsx
│   │   └── charts/
│   │       ├── RewardChart.tsx
│   │       ├── PolicyLossChart.tsx
│   │       └── PerformanceChart.tsx
│   ├── hooks/            # Custom React hooks
│   │   ├── useGameState.ts
│   │   ├── useRunList.ts
│   │   └── useWebSocket.ts
│   ├── contexts/         # React contexts
│   │   └── RunContext.tsx
│   ├── services/         # API clients
│   │   └── api.ts
│   └── types/            # TypeScript types
│       └── index.ts
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── README.md
```

## Features (To Be Implemented)

- [ ] Run selector dropdown
- [ ] Real-time colonist monitoring
- [ ] Training metrics visualization
- [ ] Active threat monitoring
- [ ] Multi-run comparison view
- [ ] Historical data charts
- [ ] WebSocket live updates (2Hz)

## License

MIT License - See main project LICENSE
