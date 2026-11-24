import { useMemo } from 'react';
import { ReactFlow, Background, Controls } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import StageNode from './StageNode';
import { useBreakerSocket } from './useBreakerSocket';

const nodeTypes = { stage: StageNode };

const baseNodes = [
  { id: 'ingest',  type: 'stage', position: { x: 50,  y: 120 }, data: { label: 'Ingest (Kafka)',  status: 'healthy' } },
  { id: 'process', type: 'stage', position: { x: 300, y: 120 }, data: { label: 'Process (Flink)', status: 'healthy' } },
  { id: 'serve',   type: 'stage', position: { x: 550, y: 120 }, data: { label: 'Serve (Iceberg)', status: 'healthy' } },
];

const edges = [
  { id: 'e1', source: 'ingest',  target: 'process', animated: true },
  { id: 'e2', source: 'process', target: 'serve',   animated: true },
];

const PROCESS_STATUS = { CLOSED: 'healthy', HALF_OPEN: 'warning', OPEN: 'quarantined' };
const SERVE_STATUS   = { CLOSED: 'healthy', HALF_OPEN: 'warning', OPEN: 'warning' };

export default function App() {
  const { breaker } = useBreakerSocket('ws://localhost:8000/ws');

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
    <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      <div style={{
        position: 'absolute', zIndex: 10, top: 12, left: 12, background: '#fff',
        padding: '8px 12px', borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.15)', fontFamily: 'sans-serif',
      }}>
        Circuit breaker: <b>{breaker.state}</b> · error rate {(breaker.error_rate * 100).toFixed(1)}%
      </div>
      <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView>
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}