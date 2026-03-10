import './Dashboard.css'
import GreetingsHeader from './GreetingsHeader'
import StatusCard from './StatusCard'
import { useState } from 'react'
import { Mic, Monitor, Music, Code } from 'lucide-react'

export default function Dashboard() {
  const [isListening, setIsListening] = useState(false);

  // For visual demonstration
  const handleToggle = () => setIsListening(!isListening);

  return (
    <div className="dashboard-container" onClick={handleToggle}>
      <div className="dashboard-content">
        <GreetingsHeader />
        
        <div className="center-container">
          {!isListening ? (
            <div className="mission-label">WOLF AI IS READY FOR ASSIGNMENT.</div>
          ) : (
            <div className="listening-badge">
              <span className="listening-icon">🎙️</span> LISTENING...
            </div>
          )}
        </div>

        <div className="status-grid">
          <StatusCard icon={<Mic size={28} />} title="Voice Core" status={isListening ? "ACTIVE" : "LISTENING"} color={isListening ? "var(--accent-pink)" : "var(--accent-cyan)"} />
          <StatusCard icon={<Monitor size={28} />} title="System Control" status="READY" color="#00ff9d" />
          <StatusCard icon={<Music size={28} />} title="Neural Sonic" status="STANDBY" color="var(--accent-pink)" />
          <StatusCard icon={<Code size={28} />} title="Dev Agent" status="IDLE" color="var(--accent-purple)" />
        </div>
      </div>
    </div>
  )
}
