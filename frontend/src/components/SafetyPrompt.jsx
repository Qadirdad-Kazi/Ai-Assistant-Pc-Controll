import { AlertTriangle, Check, X, ShieldAlert } from 'lucide-react';
import { useEffect, useState } from 'react';
import './SafetyPrompt.css';
import { wsUrl } from '../utils/api';

export default function SafetyPrompt() {
  const [activePrompt, setActivePrompt] = useState(null);
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    const ws = new WebSocket(wsUrl('/ws/safety'));
    
    ws.onopen = () => {
      console.log('[Safety] Connected to safety sandbox stream');
      setSocket(ws);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'CONFIRMATION_REQUIRED') {
          setActivePrompt(data);
          // Play a subtle alert sound if possible
          try { new Audio('/alert.mp3').play(); } catch(e) {}
        }
      } catch (err) {
        console.error('[Safety] Stream parse failed', err);
      }
    };

    ws.onclose = () => {
      console.warn('[Safety] Disconnected from safety sandbox');
      // Reconnect logic usually handled by a wrapper, but for now:
      setTimeout(() => setSocket(null), 2000);
    };

    return () => {
      if (ws.readyState === 1) ws.close();
    };
  }, []);

  const handleResponse = (approved) => {
    if (!socket || !activePrompt) return;
    
    socket.send(JSON.stringify({
      id: activePrompt.id,
      approved: approved
    }));
    
    setActivePrompt(null);
  };

  if (!activePrompt) return null;

  return (
    <div className="safety-overlay">
      <div className="safety-modal">
        <div className="safety-header">
          <div className="safety-icon-wrapper">
            <ShieldAlert size={32} className="pulse-icon" />
          </div>
          <div className="safety-title">
            <h3>Manual Approval Required</h3>
            <span className="safety-subtitle">Security Sandbox Layer</span>
          </div>
        </div>

        <div className="safety-body">
          <p className="safety-message">
            Wolf AI is requesting permission to perform a high-risk system command:
          </p>
          <div className="action-details">
            <span className="action-name">{activePrompt.action}</span>
            {activePrompt.details && (
              <code className="action-code">{activePrompt.details}</code>
            )}
          </div>
          <p className="safety-warning">
            <AlertTriangle size={14} style={{marginRight: '6px'}} />
            Continuing may modify system state or close active applications.
          </p>
        </div>

        <div className="safety-footer">
          <button className="safety-btn block-btn" onClick={() => handleResponse(false)}>
            <X size={18} /> BLOCK ACTION
          </button>
          <button className="safety-btn approve-btn" onClick={() => handleResponse(true)}>
            <Check size={18} /> APPROVE ACTION
          </button>
        </div>
      </div>
    </div>
  );
}
