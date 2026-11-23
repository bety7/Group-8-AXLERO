import { Handle, Position } from '@xyflow/react';

const COLORS = {
  healthy: '#16a34a',
  warning: '#f59e0b',
  quarantined: '#dc2626',
};

export default function StageNode({ data }) {
  const color = COLORS[data.status] ?? COLORS.healthy;
  return (
    <div style={{
      padding: '12px 18px',
      borderRadius: 10,
      background: '#fff',
      border: `3px solid ${color}`,
      minWidth: 140,
      textAlign: 'center',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    }}>
      <Handle type="target" position={Position.Left} />
      <div style={{ fontWeight: 700 }}>{data.label}</div>
      <div style={{ fontSize: 12, color }}>{data.status}</div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}