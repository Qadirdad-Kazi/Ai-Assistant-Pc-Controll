import './Dashboard.css'
import GreetingsHeader from './GreetingsHeader'
import StatusCard from './StatusCard'
import { useState } from 'react'
import { Mic, Monitor, Music, Code } from 'lucide-react'

export default function Dashboard() {
  const [isListening, setIsListening] = useState(false);
  const [statuses, setStatuses] = useState({
    "Voice Core": "OFFLINE",
    "System Control": "READY",
    "Neural Sonic": "STANDBY",
    "Dev Agent": "IDLE"
  });

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/status');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setIsListening(data.isListening);
      setStatuses(data);
    };

    ws.onerror = (error) => {
      console.error("Status WebSocket error:", error);
    };

    return () => {
      if (ws.readyState === 1) ws.close();
    };
  }, []);

  // Removed clicking toggle since we're tied to backend now
  return (
    <div className="dashboard-container">
      <div className="dashboard-content">
        <GreetingsHeader />
        
        <div className="center-container">
          {!isListening ? (
            <div className="mission-label"></div>
          ) : (
            <div className="blob-container">
              <div className="blob"></div>
              <div className="blob-core">
                <Mic size={48} className="blob-icon" />
              </div>
            </div>
          )}
        </div>

        <div className="status-grid">
          <StatusCard icon={<Mic size={28} />} title="Voice Core" status={statuses["Voice Core"]} color={isListening ? "var(--accent-pink)" : "var(--accent-cyan)"} />
          <StatusCard icon={<Monitor size={28} />} title="System Control" status={statuses["System Control"]} color="#00ff9d" />
          <StatusCard icon={<Music size={28} />} title="Neural Sonic" status={statuses["Neural Sonic"]} color="var(--accent-pink)" />
          <StatusCard icon={<Code size={28} />} title="Dev Agent" status={statuses["Dev Agent"]} color="var(--accent-purple)" />
        </div>
      </div>
    </div>
  )
}
