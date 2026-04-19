import { RefreshCw, PhoneForwarded } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import './CallLogs.css';
import { apiUrl, wsUrl } from '../utils/api';

export default function CallLogs() {
  const [logs, setLogs] = useState([]);
  const [expanded, setExpanded] = useState({});
  const [statusFilter, setStatusFilter] = useState('all');
  const [isLoading, setIsLoading] = useState(true);

  const fetchLogs = async () => {
    try {
      const res = await fetch(apiUrl('/api/call-logs?limit=200'));
      const data = await res.json();
      setLogs(data.logs || []);
    } catch (err) {
      console.error('Failed to fetch call logs', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  useEffect(() => {
    const ws = new WebSocket(wsUrl('/ws/call-logs'));
    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.logs) {
          setLogs(payload.logs);
          setIsLoading(false);
        }
      } catch (err) {
        console.error('Failed to parse call logs stream payload', err);
      }
    };

    ws.onerror = (err) => {
      console.error('Call logs WebSocket error', err);
    };

    return () => {
      if (ws.readyState === 1) ws.close();
    };
  }, []);

  const formatTime = (ts) => {
    if (!ts) return 'Unknown time';
    const d = new Date(ts);
    if (Number.isNaN(d.getTime())) return ts;
    return d.toLocaleString();
  };

  const filteredLogs = useMemo(() => {
    if (statusFilter === 'all') return logs;
    return logs.filter((l) => String(l.status || '').toLowerCase() === statusFilter.toLowerCase());
  }, [logs, statusFilter]);

  const statusOptions = useMemo(() => {
    const unique = new Set(logs.map((l) => String(l.status || 'Unknown')));
    return ['all', ...Array.from(unique)];
  }, [logs]);

  const toggleExpanded = (logId) => {
    setExpanded((prev) => ({ ...prev, [logId]: !prev[logId] }));
  };

  return (
    <div className="call-logs-container">
      <div className="call-logs-header">
        <div>
          <h2>RECEPTIONIST LOGS</h2>
          <p className="subtitle">GSM INTERCEPTS & COMMUNICATION TRANSCRIPTS</p>
        </div>
        <button className="refresh-btn" onClick={fetchLogs}>
          <RefreshCw size={18} style={{marginRight: '8px'}} /> REFRESH LOGS
        </button>
      </div>

      <div className="call-logs-toolbar">
        <label htmlFor="statusFilter">Filter:</label>
        <select id="statusFilter" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          {statusOptions.map((status) => (
            <option key={status} value={status}>{status.toUpperCase()}</option>
          ))}
        </select>
        <span className="logs-count">Showing {filteredLogs.length} of {logs.length}</span>
      </div>

      <div className="logs-panel">
        {isLoading ? (
          <div className="empty-state">Loading call logs...</div>
        ) : filteredLogs.length === 0 ? (
          <div className="empty-state">No phone calls have been logged yet.</div>
        ) : (
          filteredLogs.map((log) => (
            <div key={log.id} className="log-item">
              <div className="log-header">
                <div className="caller-info">
                  <PhoneForwarded size={16} />
                  <strong>[GSM GATEWAY] Incoming Call from {String(log.caller || 'Unknown').toUpperCase()}</strong>
                </div>
                <div className="log-time">{formatTime(log.timestamp)}</div>
              </div>
              <div className="log-meta-row">
                <span className={`status-chip status-${String(log.status || 'unknown').toLowerCase().replace(/\s+/g, '-')}`}>{log.status || 'Unknown'}</span>
                <span className="log-meta">Intent: {log.instructions || 'No instructions'}</span>
                {log.client_mood && (
                  <span className={`mood-chip mood-${String(log.client_mood).toLowerCase()}`}>
                    Mood: {log.client_mood}
                  </span>
                )}
                {log.document_path && (
                  <a
                    href={apiUrl(`/api/documents/proposals/${encodeURIComponent((String(log.document_path).split('/').pop() || '').trim())}`)}
                    target="_blank"
                    rel="noreferrer"
                    className="proposal-link"
                  >
                    View Proposal
                  </a>
                )}
              </div>
              <div className="log-transcript">
                <strong>Transcript:</strong><br/>
                {expanded[log.id] ? (log.transcript || 'No transcript') : `${(log.transcript || 'No transcript').slice(0, 220)}${(log.transcript || '').length > 220 ? '...' : ''}`}
              </div>
              {(log.transcript || '').length > 220 && (
                <button className="transcript-toggle" onClick={() => toggleExpanded(log.id)}>
                  {expanded[log.id] ? 'Show Less' : 'Show More'}
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
