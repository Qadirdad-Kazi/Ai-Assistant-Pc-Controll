import React, { useEffect, useState } from 'react';
import { Calendar, Bell, X, PhoneCall, CheckCircle } from 'lucide-react';
import './CalendarReminder.css';
import { wsUrl } from '../utils/api';

export default function CalendarReminder() {
  const [reminder, setReminder] = useState(null);

  useEffect(() => {
    const ws = new WebSocket(wsUrl('/ws/safety')); // Listening on safety stream for reminders
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'CALENDAR_REMINDER') {
          setReminder(data);
          // Auto-hide after 30 seconds
          setTimeout(() => setReminder(null), 30000);
        }
      } catch (err) {
        console.error('[CalendarReminder] WebSocket parse error:', err);
      }
    };

    return () => {
      if (ws.readyState === 1) ws.close();
    };
  }, []);

  if (!reminder) return null;

  return (
    <div className="calendar-reminder-container">
      <div className="calendar-reminder-card">
        <div className="reminder-header">
          <div className="reminder-icon">
            <Calendar size={20} />
          </div>
          <span className="reminder-label">Upcoming Call Detected</span>
          <button className="close-btn" onClick={() => setReminder(null)}>
            <X size={16} />
          </button>
        </div>
        
        <div className="reminder-body">
          <div className="caller-info">
            <PhoneCall size={24} className="pulse-icon" />
            <div className="caller-details">
              <h4>{reminder.caller}</h4>
              <p>{reminder.time}</p>
            </div>
          </div>
          
          <div className="instructions-section">
            <span className="section-label">AI Action Plan:</span>
            <div className="instruction-bubble">
              {reminder.instructions}
            </div>
          </div>
        </div>

        <div className="reminder-footer">
          <div className="status-badge">
            <CheckCircle size={14} />
            <span>Wolf AI Prepared</span>
          </div>
          <button className="confirm-btn" onClick={() => setReminder(null)}>
            GOT IT
          </button>
        </div>
      </div>
    </div>
  );
}
