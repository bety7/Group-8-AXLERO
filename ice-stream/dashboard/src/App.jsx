import { ReactFlow, Background, Controls } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import StageNode from './StageNode';

const nodeTypes = { stage: StageNode };

const nodes = [
  { id: 'ingest',  type: 'stage', position: { x: 50,  y: 120 }, data: { label: 'Ingest (Kafka)',  status: 'healthy' } },
  { id: 'process', type: 'stage', position: { x: 300, y: 120 }, data: { label: 'Process (Flink)', status: 'healthy' } },
  { id: 'serve',   type: 'stage', position: { x: 550, y: 120 }, data: { label: 'Serve (Iceberg)', status: 'healthy' } },
];

const edges = [
  { id: 'e1', source: 'ingest',  target: 'process', animated: true },
  { id: 'e2', source: 'process', target: 'serve',   animated: true },
];

export default function App() {
  return (
    <div style={{ width: '100vw', height: '100vh' }}>
      <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView>
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}