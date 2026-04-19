import { Shield, ArrowUp, ArrowDown, Database, Activity, Trash2 } from 'lucide-react';
import { useEffect, useState, useMemo } from 'react';
import './Privacy.css';
import { apiUrl, wsUrl } from '../utils/api';

export default function Privacy() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    try {
      const res = await fetch(apiUrl('/api/privacy/logs'));
      const data = await res.json();
      setLogs(data.logs || []);
    } catch (err) {
      console.error('Failed to fetch privacy logs', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    
    // Subscribe to real-time logs
    const ws = new WebSocket(wsUrl('/ws/privacy'));
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data?.logs) {
          setLogs(data.logs);
        }
      } catch (err) {
        console.error('Privacy stream parse failed', err);
      }
    };

    return () => {
      if (ws.readyState === 1) ws.close();
    };
  }, []);

  const stats = useMemo(() => {
    const sent = logs.filter(l => l.direction === 'SENT').length;
    const received = logs.filter(l => l.direction === 'RECEIVED').length;
    const totalSize = logs.reduce((acc, l) => acc + (l.size || 0), 0);
    
    // Group by service
    const serviceCounts = {};
    logs.forEach(l => {
      serviceCounts[l.service] = (serviceCounts[l.service] || 0) + 1;
    });
    
    const topService = Object.entries(serviceCounts)
      .sort((a, b) => b[1] - a[1])[0]?.[0] || 'None';

    return { sent, received, totalSize, topService };
  }, [logs]);

  const formatSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const clearLogs = async () => {
      // In a real app, this would call an API
      setLogs([]);
  };

  return (
    <div className="privacy-container">
      <div className="privacy-header">
        <div className="title-area">
          <div className="icon-badge"><Shield size={24} /></div>
          <div>
            <h2>PRIVACY & DATA DASHBOARD</h2>
            <p className="subtitle">Real-time monitoring of all outbound and inbound data flow</p>
          </div>
        </div>
        <div className="header-actions">
           <button className="clear-btn" onClick={clearLogs}><Trash2 size={18} /> Clear Session</button>
        </div>
      </div>

      <div className="privacy-stats-grid">
        <div className="stat-card">
          <div className="stat-icon"><ArrowUp size={20} className="sent-col" /></div>
          <div className="stat-content">
            <span className="stat-label">DATA SENT</span>
            <span className="stat-value">{stats.sent} events</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><ArrowDown size={20} className="received-col" /></div>
          <div className="stat-content">
            <span className="stat-label">DATA RECEIVED</span>
            <span className="stat-value">{stats.received} events</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><Database size={20} className="total-col" /></div>
          <div className="stat-content">
            <span className="stat-label">TOTAL VOLUME</span>
            <span className="stat-value">{formatSize(stats.totalSize)}</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><Activity size={20} className="active-col" /></div>
          <div className="stat-content">
            <span className="stat-label">TOP SERVICE</span>
            <span className="stat-value">{stats.topService}</span>
          </div>
        </div>
      </div>

      <div className="privacy-log-area">
        <div className="log-header">
          <h3>Activity Feed</h3>
          <span className="log-count">{logs.length} Total Events</span>
        </div>
        
        <div className="log-table-wrapper">
          <table className="privacy-table">
            <thead>
              <tr>
                <th>TIME</th>
                <th>SERVICE</th>
                <th>DIRECTION</th>
                <th>TYPE</th>
                <th>SUMMARY</th>
                <th>SIZE</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td colSpan="6" className="no-data">No data flow detected yet. All communications are verified and secure.</td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id}>
                    <td className="time-col">{new Date(log.timestamp).toLocaleTimeString()}</td>
                    <td><span className={`service-pill pill-${String(log.service || 'unknown').toLowerCase().replace(/\s+/g, '-')}`}>{log.service || 'Unknown'}</span></td>
                    <td>
                      <span className={`direction-pill ${String(log.direction || 'unknown').toLowerCase()}`}>
                        {String(log.direction || '').toUpperCase() === 'SENT' ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
                        {log.direction || 'UNKNOWN'}
                      </span>
                    </td>
                    <td>{log.type}</td>
                    <td className="summary-col">{log.summary}</td>
                    <td className="size-col">{formatSize(log.size)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
