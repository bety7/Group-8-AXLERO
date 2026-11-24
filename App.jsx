import React, { useEffect, useState } from 'react';
import { ReactFlow, Background, Controls, MiniMap } from '@xyflow/react';
import { Activity, AlertTriangle, CheckCircle2, PauseCircle, Play, Camera, RefreshCw, Database, Radio, ShieldCheck } from 'lucide-react';

const API = 'http://localhost:8000';
const initialNodes = [
  { id:'ingest', position:{x:30,y:130}, data:{label:'INGEST\\nKafka / Redpanda'}, style:{background:'#e8f1ff',border:'1px solid #7aa7e8',borderRadius:12,padding:14,width:175,whiteSpace:'pre-line',fontWeight:700}},
  { id:'process', position:{x:285,y:130}, data:{label:'PROCESS\\nRules + stream checks'}, style:{background:'#e9f8ef',border:'1px solid #68b58a',borderRadius:12,padding:14,width:190,whiteSpace:'pre-line',fontWeight:700}},
  { id:'serve', position:{x:570,y:55}, data:{label:'SERVE\\nTrusted records'}, style:{background:'#e9f8ef',border:'1px solid #68b58a',borderRadius:12,padding:14,width:175,whiteSpace:'pre-line',fontWeight:700}},
  { id:'quarantine', position:{x:570,y:235}, data:{label:'QUARANTINE / DLQ\\nRejected records'}, style:{background:'#fff0ed',border:'1px solid #e58b7b',borderRadius:12,padding:14,width:205,whiteSpace:'pre-line',fontWeight:700}}
];
const edges = [
  {id:'e1',source:'ingest',target:'process',animated:true,label:'events'},
  {id:'e2',source:'process',target:'serve',animated:true,label:'valid'},
  {id:'e3',source:'process',target:'quarantine',animated:true,label:'invalid / paused',style:{stroke:'#d65b4a'},labelStyle:{fill:'#b94435'}}
];

export default function App(){
  const [status,setStatus]=useState({status:'CONNECTING',total:0,valid:0,bad:0,quarantined:0,bad_rate:0,threshold:.02,events:[],incidents:[]});
  const [incidents,setIncidents]=useState([]);
  const [snapshots,setSnapshots]=useState([]);
  const [busy,setBusy]=useState(false);
  async function refresh(){
    try{
      const [s,i,ss]=await Promise.all([fetch(`${API}/api/status`),fetch(`${API}/api/incidents`),fetch(`${API}/api/snapshots`)]);
      setStatus(await s.json()); setIncidents(await i.json()); setSnapshots(await ss.json());
    }catch(e){setStatus(v=>({...v,status:'API OFFLINE'}));}
  }
  useEffect(()=>{
    refresh();
    const timer=setInterval(refresh,2500);
    let ws;
    try{ws=new WebSocket('ws://localhost:8000/ws');ws.onmessage=e=>setStatus(JSON.parse(e.data));}catch(e){}
    return ()=>{clearInterval(timer);ws?.close();};
  },[]);
  async function action(path){
    setBusy(true);try{await fetch(`${API}${path}`,{method:'POST'});await refresh();}finally{setBusy(false);}
  }
  const paused=status.status==='PAUSED';
  const nodes=initialNodes.map(n=>n.id==='process'?{...n,style:{...n.style,background:paused?'#fff0ed':'#e9f8ef',borderColor:paused?'#d65b4a':'#68b58a'}}:n);
  return <div className="app">
    <header><div className="brand"><div className="logo"><Database size={22}/></div><div><h1>ICE STREAM</h1><p>REAL-TIME LAKEHOUSE OBSERVABILITY</p></div></div><div className={`pill ${paused?'danger':'good'}`}><span/> {status.status}</div></header>
    <main>
      <section className="intro"><div><div className="eyebrow">DATA ARCHITECTURE & RELIABILITY ENGINEERING</div><h2>Pipeline control center</h2><p>Monitor streaming quality, detect anomalies and isolate bad data before it reaches analytics.</p></div><div className="actions"><button onClick={()=>action('/api/pipeline/resume')} disabled={busy}><Play size={16}/> Resume pipeline</button><button className="secondary" onClick={()=>action('/api/snapshots')} disabled={busy}><Camera size={16}/> Create snapshot</button><button className="iconbtn" onClick={refresh}><RefreshCw size={17}/></button></div></section>
      <section className="metrics">
        <Metric icon={<Activity/>} label="Events processed" value={status.total??0}/>
        <Metric icon={<CheckCircle2/>} label="Trusted / served" value={status.valid??0}/>
        <Metric icon={<AlertTriangle/>} label="Bad records" value={status.bad??0}/>
        <Metric icon={<ShieldCheck/>} label="Quarantined" value={status.quarantined??0}/>
      </section>
      <section className="grid">
        <div className="panel pipeline"><div className="panelhead"><div><h3>Data lineage</h3><p>Live movement through the streaming pipeline</p></div><span className="live"><i/> LIVE</span></div><div className="flow"><ReactFlow nodes={nodes} edges={edges} fitView fitViewOptions={{padding:.2}} nodesDraggable={false} nodesConnectable={false}><Background/><Controls/><MiniMap/></ReactFlow></div>
          {paused&&<div className="alert"><PauseCircle/><div><b>Circuit breaker is OPEN</b><p>{status.paused_reason||'Bad-data threshold exceeded. Downstream serving is paused.'}</p></div></div>}
        </div>
        <div className="panel quality"><div className="panelhead"><div><h3>Quality guardrails</h3><p>Rolling validation window</p></div></div><div className="rate"><strong>{((status.bad_rate||0)*100).toFixed(1)}%</strong><span>Current bad-data rate</span></div><div className="bar"><span style={{width:`${Math.min(100,(status.bad_rate||0)/Math.max(status.threshold||.02,.001)*100)}%`}}/></div><div className="threshold"><span>Configured threshold</span><b>{((status.threshold||.02)*100).toFixed(1)}%</b></div><div className="rule"><CheckCircle2/> Required fields & schema</div><div className="rule"><CheckCircle2/> Amount not null / numeric</div><div className="rule"><CheckCircle2/> Amount must be non-negative</div></div>
      </section>
      <section className="grid lower">
        <div className="panel"><div className="panelhead"><div><h3>Incident log</h3><p>Automated detection and operator actions</p></div><span className="count">{incidents.length}</span></div>{incidents.length===0?<div className="empty">No incidents recorded yet. Generate events to test the rules engine.</div>:<div className="list">{incidents.slice(0,8).map(x=><div className="incident" key={x.id}><AlertTriangle size={17}/><div><b>{x.type.replaceAll('_',' ')}</b><p>{x.message}</p><small>{new Date(x.timestamp).toLocaleString()}</small></div></div>)}</div>}</div>
        <div className="panel"><div className="panelhead"><div><h3>Time-travel snapshots</h3><p>Point-in-time serving data copies</p></div><button className="small" onClick={()=>action('/api/snapshots')}><Camera size={14}/> Snapshot</button></div>{snapshots.length===0?<div className="empty">No snapshots yet. Create one to preserve the current serving state.</div>:<div className="list">{snapshots.slice(0,6).map(s=><div className="snapshot" key={s.snapshot_id}><Database size={17}/><div><b>{s.snapshot_id}</b><p>{s.records} records · {new Date(s.created_at).toLocaleString()}</p><a href={`${API}/api/time-travel/${s.snapshot_id}`} target="_blank">View snapshot data ↗</a></div></div>)}</div>}</div>
      </section>
      <footer><span><Radio size={15}/> Kafka-compatible ingestion</span><span>Python rules engine</span><span>Flink / Iceberg target architecture</span><span>React Flow lineage</span></footer>
    </main>
  </div>
}
function Metric({icon,label,value}){return <div className="metric"><div className="metricicon">{icon}</div><div><span>{label}</span><strong>{value.toLocaleString()}</strong></div></div>}
