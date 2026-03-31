import { HelpCircle, Check, X, MousePointer2 } from 'lucide-react';
import { useEffect, useState, useRef } from 'react';
import './ClarificationPrompt.css';

export default function ClarificationPrompt() {
  const [activePrompt, setActivePrompt] = useState(null);
  const [socket, setSocket] = useState(null);
  const imageRef = useRef(null);

  useEffect(() => {
    // Port 8000 is our FastAPI backend
    const ws = new WebSocket('ws://localhost:8000/ws/clarification');
    
    ws.onopen = () => {
      console.log('[Clarification] Connected to visual bridge');
      setSocket(ws);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'CLARIFICATION_REQUIRED') {
          setActivePrompt(data);
          // Alert sound
          try { new Audio('/notification.mp3').play(); } catch(e) {}
        }
      } catch (err) {
        console.error('[Clarification] Stream parse failed', err);
      }
    };

    ws.onclose = () => {
      console.warn('[Clarification] Disconnected');
      setTimeout(() => setSocket(null), 2000);
    };

    return () => {
      if (ws.readyState === 1) ws.close();
    };
  }, []);

  const handleResponse = (result) => {
    if (!socket || !activePrompt) return;
    
    socket.send(JSON.stringify({
      id: activePrompt.id,
      result: result
    }));
    
    setActivePrompt(null);
  };

  const handleImageClick = (e) => {
    if (!imageRef.current || !activePrompt) return;
    
    const rect = imageRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    
    handleResponse({
      success: true,
      mode: 'point',
      x_percent: x,
      y_percent: y,
      message: 'User pointed to location'
    });
  };

  if (!activePrompt) return null;

  return (
    <div className="clarification-overlay">
      <div className="clarification-modal">
        <div className="clarification-header">
          <div className="clarification-icon-wrapper">
            <HelpCircle size={32} className="pulse-icon-blue" />
          </div>
          <div className="clarification-title">
            <h3>Visual Clarification Required</h3>
            <span className="clarification-subtitle">Human-in-the-loop Grounding</span>
          </div>
        </div>

        <div className="clarification-body">
          <p className="clarification-question">
            {activePrompt.question || "I'm unsure about an element on your screen. Could you clarify?"}
          </p>
          
          <div className="screenshot-container" onClick={handleImageClick}>
            <img 
              ref={imageRef}
              src={`data:image/png;base64,${activePrompt.screenshot}`} 
              alt="Screen Context" 
              className="clarification-image"
            />
            <div className="overlay-instruction">
              <MousePointer2 size={16} /> Click precisely on the element you meant
            </div>
          </div>
        </div>

        <div className="clarification-footer">
          <button className="clarification-btn cancel-btn" onClick={() => handleResponse({success: false, message: 'User cancelled'})}>
            <X size={18} /> ABORT TASK
          </button>
          <div className="footer-right">
             <button className="clarification-btn neutral-btn" onClick={() => handleResponse({success: true, mode: 'confirm', message: 'User confirmed generic presence'})}>
              <Check size={18} /> YES, PROCEED
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
