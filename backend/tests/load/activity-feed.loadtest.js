import { check } from 'k6';
import ws from 'k6/ws';
import { Rate } from 'k6/metrics';

const WS_URL = __ENV.WS_URL || 'ws://localhost:3001';

const MARKET_COUNT = 20;
const MARKET_IDS = Array.from({ length: MARKET_COUNT }, (_, i) => `loadtest-mkt-${i}`);

export const errorRate = new Rate('errors');

export const options = {
  scenarios: {
    connections: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 100 },
        { duration: '30s', target: 100 },
        { duration: '10s', target: 0 },
      ],
      gracefulStop: '5s',
    },
  },
  thresholds: {
    ws_connecting: ['p(95)<200'],
    ws_sessions: ['count>0'],
    checks: ['rate>0.99'],
    errors: ['rate==0'],
  },
};

export default function () {
  const selected = [];
  while (selected.length < 5) {
    const m = MARKET_IDS[Math.floor(Math.random() * MARKET_COUNT)];
    if (!selected.includes(m)) selected.push(m);
  }

  const res = ws.connect(WS_URL, {}, function (socket) {
    socket.on('open', function () {
      for (const marketId of selected) {
        socket.send(JSON.stringify({ type: 'subscribe_activity', marketId }));
      }
    });

    socket.on('message', function (_data) {
      // Activity feed updates received
    });

    socket.on('error', function (e) {
      errorRate.add(1);
      console.error(`WS error: ${JSON.stringify(e)}`);
    });

    socket.setTimeout(function () {
      socket.close();
    }, 15000);
  });

  const checkSuccess = check(res, {
    'WebSocket handshake succeeded': (r) => r && r.status === 101,
  });

  if (!checkSuccess) {
    errorRate.add(1);
  } else {
    errorRate.add(0);
  }
}
