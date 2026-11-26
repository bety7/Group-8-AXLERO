import { useEffect, useState } from 'react';

function formatDuration(ms) {
  const s = Math.max(0, Math.round(ms / 1000));
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
}

export default function IncidentLog({ refreshKey }) {
  const [incidents, setIncidents] = useState([]);

  useEffect(() => {
    let cancelled = false;
    const load = () =>
      fetch('http://localhost:8000/incidents')
        .then((r) => r.json())
        .then((d) => { if (!cancelled) setIncidents(d); })
        .catch(() => {});
    load();
    const timer = setInterval(load, 5000);
    return () => { cancelled = true; clearInterval(timer); };
  }, [refreshKey]);

  return (
    <div className="incident-log">
      <h3>Incident log</h3>
      {incidents.length === 0 ? (
        <p>No incidents yet.</p>
      ) : (
        <table>
          <thead>
            <tr><th>Status</th><th>Paused at</th><th>Resumed at</th><th>Duration</th><th>Error rate</th><th>Why</th></tr>
          </thead>
          <tbody>
            {incidents.map((i) => {
              const active = !i.resumed_at;
              const end = active ? Date.now() : new Date(i.resumed_at).getTime();
              return (
                <tr key={i.id}>
                  <td><span className={`badge ${active ? 'badge-active' : 'badge-resolved'}`}>{active ? 'Paused' : 'Resumed'}</span></td>
                  <td>{new Date(i.paused_at).toLocaleTimeString()}</td>
                  <td>{active ? '—' : new Date(i.resumed_at).toLocaleTimeString()}</td>
                  <td>{formatDuration(end - new Date(i.paused_at).getTime())}</td>
                  <td>{(i.error_rate * 100).toFixed(1)}%</td>
                  <td>{i.reason}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}