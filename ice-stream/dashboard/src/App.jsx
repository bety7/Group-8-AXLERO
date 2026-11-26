import { useMemo } from 'react';
import { ReactFlow, Background, Controls } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import StageNode from './StageNode';
import IncidentLog from './IncidentLog';
import { useBreakerSocket } from './useBreakerSocket';

const nodeTypes = { stage: StageNode };

const baseNodes = [
  { id: 'ingest',  type: 'stage', position: { x: 50,  y: 80 }, data: { label: 'Ingest (Kafka)',  status: 'healthy' } },
  { id: 'process', type: 'stage', position: { x: 300, y: 80 }, data: { label: 'Process (Flink)', status: 'healthy' } },
  { id: 'serve',   type: 'stage', position: { x: 550, y: 80 }, data: { label: 'Serve (Iceberg)', status: 'healthy' } },
];

const edges = [
  { id: 'e1', source: 'ingest',  target: 'process', animated: true },
  { id: 'e2', source: 'process', target: 'serve',   animated: true },
];

const PROCESS_STATUS = { CLOSED: 'healthy', HALF_OPEN: 'warning', OPEN: 'quarantined' };
const SERVE_STATUS   = { CLOSED: 'healthy', HALF_OPEN: 'warning', OPEN: 'warning' };

export default function App() {
  const { breaker, connected } = useBreakerSocket('ws://localhost:8000/ws');

  const nodes = useMemo(
    () =>
      baseNodes.map((n) => {
        if (n.id === 'process') return { ...n, data: { ...n.data, status: PROCESS_STATUS[breaker.state] ?? 'healthy' } };
        if (n.id === 'serve')   return { ...n, data: { ...n.data, status: SERVE_STATUS[breaker.state] ?? 'healthy' } };
        return n;
      }),
    [breaker.state]
  );

  return (
    <div className="layout">
      <div className="canvas">
        <div className="banner">
          Circuit breaker: <b>{breaker.state}</b> · error rate {(breaker.error_rate * 100).toFixed(1)}%
          {!connected && <span className="offline"> · reconnecting…</span>}
        </div>
        <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView>
          <Background />
          <Controls />
        </ReactFlow>
      </div>
      <IncidentLog refreshKey={breaker.state} />
    </div>
  );
}