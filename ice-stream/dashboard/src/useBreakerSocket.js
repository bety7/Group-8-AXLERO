import { useEffect, useState } from 'react';

export function useBreakerSocket(url) {
  const [breaker, setBreaker] = useState({ state: 'CLOSED', error_rate: 0 });
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let ws;
    let timer;
    let closedByUs = false;

    const connect = () => {
      ws = new WebSocket(url);
      ws.onopen = () => setConnected(true);
      ws.onmessage = (e) => {
        const m = JSON.parse(e.data);
        if (m.type === 'snapshot') setBreaker({ state: m.state, error_rate: m.error_rate });
        else if (m.type === 'breaker') setBreaker({ state: m.to, error_rate: m.error_rate });
      };
      ws.onclose = () => {
        setConnected(false);
        if (!closedByUs) timer = setTimeout(connect, 2000);
      };
    };

    connect();
    return () => {
      closedByUs = true;
      clearTimeout(timer);
      if (ws) ws.close();
    };
  }, [url]);

  return { breaker, connected };
}