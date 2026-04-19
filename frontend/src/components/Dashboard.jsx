import './Dashboard.css'
import GreetingsHeader from './GreetingsHeader'
import StatusCard from './StatusCard'
import SystemMonitor from './SystemMonitor'
import { useState, useEffect } from 'react'
import { Mic, Monitor, Music, Code, Phone } from 'lucide-react'
import { wsUrl } from '../utils/api'

export default function Dashboard() {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [statuses, setStatuses] = useState({
    "Voice Core": "OFFLINE",
    "System Control": "READY",
    "Neural Sonic": "STANDBY",
    "Dev Agent": "IDLE",
    "Call Status": "IDLE"
  });

  useEffect(() => {
    const ws = new WebSocket(wsUrl('/ws/status'));
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setIsListening(data.isListening);
      setStatuses(data);
      
      // Determine AI state based on system status
      const voiceCoreStatus = data["Voice Core"];
      const neuralSonicStatus = data["Neural Sonic"];
      
      // User speaking when isListening is true
      // AI processing when Voice Core is "PROCESSING" or similar
      // AI speaking when Neural Sonic is "PLAYING"
      setIsProcessing(voiceCoreStatus === "PROCESSING" || voiceCoreStatus === "THINKING");
      setIsSpeaking(neuralSonicStatus === "PLAYING");
    };

    ws.onerror = (error) => {
      console.error("Status WebSocket error:", error);
    };

    return () => {
      if (ws.readyState === 1) ws.close();
    };
  }, []);

  // Helper functions to determine blob state and icon
  const getBlobState = () => {
    if (isSpeaking) return 'speaking';
    if (isProcessing) return 'processing';
    if (isListening) return 'listening';
    return '';
  };

  const getBlobIcon = () => {
    if (isSpeaking) {
      return <div className="sound-waves">
        <div className="wave"></div>
        <div className="wave"></div>
        <div className="wave"></div>
      </div>;
    }
    if (isProcessing) {
      return <div className="thinking-dots">
        <div className="dot"></div>
        <div className="dot"></div>
        <div className="dot"></div>
      </div>;
    }
    return <Mic size={48} className="blob-icon" />;
  };

  // Removed clicking toggle since we're tied to backend now
  return (
    <div className="dashboard-container">
      <div className="dashboard-content">
        <SystemMonitor />
        <GreetingsHeader />
        
        <div className="center-container">
          {!isListening ? (
            <div className="mission-label"></div>
          ) : (
            <div className="blob-container">
              <div className={`blob ${getBlobState()}`}></div>
              <div className={`blob-core ${getBlobState()}`}>
                {getBlobIcon()}
              </div>
            </div>
          )}
        </div>

        <div className="status-grid">
          <StatusCard icon={<Mic size={28} />} title="Voice Core" status={statuses["Voice Core"]} color={isListening ? "var(--accent-pink)" : "var(--accent-cyan)"} />
          <StatusCard icon={<Monitor size={28} />} title="System Control" status={statuses["System Control"]} color="#00ff9d" />
          <StatusCard icon={<Phone size={28} />} title="Phone Gateway" status={statuses["Call Status"]} color={statuses["Call Status"] !== "IDLE" ? "var(--accent-pink)" : "var(--accent-cyan)"} />
          <StatusCard icon={<Music size={28} />} title="Neural Sonic" status={statuses["Neural Sonic"]} color="var(--accent-pink)" />
          <StatusCard icon={<Code size={28} />} title="Dev Agent" status={statuses["Dev Agent"]} color="var(--accent-purple)" />
        </div>
      </div>
    </div>
  )
}
