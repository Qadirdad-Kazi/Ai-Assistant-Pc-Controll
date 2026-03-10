import { RefreshCw, PhoneForwarded } from 'lucide-react';
import './CallLogs.css';

export default function CallLogs() {
  const dummyLogs = [
    { id: 1, caller: 'Unknown', status: 'Completed', instructions: 'No instructions', transcript: 'Hello, this is a test call.', time: '10:45 AM' }
  ];

  return (
    <div className="call-logs-container">
      <div className="call-logs-header">
        <div>
          <h2>RECEPTIONIST LOGS</h2>
          <p className="subtitle">GSM INTERCEPTS & COMMUNICATION TRANSCRIPTS</p>
        </div>
        <button className="refresh-btn">
          <RefreshCw size={18} style={{marginRight: '8px'}} /> REFRESH LOGS
        </button>
      </div>

      <div className="logs-panel">
        {dummyLogs.length === 0 ? (
          <div className="empty-state">No phone calls have been logged yet.</div>
        ) : (
          dummyLogs.map((log) => (
            <div key={log.id} className="log-item">
              <div className="log-header">
                <div className="caller-info">
                  <PhoneForwarded size={16} />
                  <strong>[GSM GATEWAY] Incoming Call from {log.caller.toUpperCase()}</strong>
                </div>
                <div className="log-time">{log.time}</div>
              </div>
              <div className="log-meta">
                Status: {log.status} | Intent Executed: {log.instructions}
              </div>
              <div className="log-transcript">
                <strong>Transcript:</strong><br/>
                {log.transcript}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
