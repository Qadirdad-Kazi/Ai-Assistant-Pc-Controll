import { useState, useEffect } from 'react';
import { Cpu, HardDrive, Wifi } from 'lucide-react';
import './SystemMonitor.css';

export default function SystemMonitor() {
  const [cpu, setCpu] = useState(0);
  const [ram, setRam] = useState(0);
  const [netUp, setNetUp] = useState(0);
  const [netDown, setNetDown] = useState(0);

  useEffect(() => {
    // Connect to WebSocket backend
    const ws = new WebSocket('ws://localhost:8000/ws/system');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setCpu(data.cpu);
      setRam(data.ram);
      setNetUp(data.netUp);
      setNetDown(data.netDown);
    };

    ws.onerror = (error) => {
      console.error("System monitor WebSocket error:", error);
    };

    return () => {
      if (ws.readyState === 1) {
        ws.close();
      }
    };
  }, []);

  return (
    <div className="sys-monitor-container">
      <div className="sys-metric">
        <Cpu size={14} className="sys-icon cyan" />
        <span className="sys-label">CPU:</span>
        <span className="sys-value">{cpu}%</span>
      </div>
      
      <div className="sys-separator"></div>
      
      <div className="sys-metric">
        <HardDrive size={14} className="sys-icon pink" />
        <span className="sys-label">RAM:</span>
        <span className="sys-value">{ram}%</span>
      </div>
      
      <div className="sys-separator"></div>
      
      <div className="sys-metric">
        <Wifi size={14} className="sys-icon purple" />
        <span className="sys-label">NET:</span>
        <span className="sys-value">↓{netDown} Mbps  ↑{netUp} Mbps</span>
      </div>
    </div>
  );
}
