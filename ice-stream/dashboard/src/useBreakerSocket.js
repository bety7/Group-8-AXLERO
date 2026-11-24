import { useEffect, useState } from 'react';

export function useBreakerSocket(url) {
  const [breaker, setBreaker] = useState({ state: 'CLOSED', error_rate: 0 });

  useEffect(() => {
    const ws = new WebSocket(url);
    ws.onmessage = (e) => {
      const m = JSON.parse(e.data);
      if (m.type === 'snapshot') setBreaker({ state: m.state, error_rate: m.error_rate });
      else if (m.type === 'breaker') setBreaker({ state: m.to, error_rate: m.error_rate });
    };
    return () => ws.close();
  }, [url]);

  return { breaker };
}