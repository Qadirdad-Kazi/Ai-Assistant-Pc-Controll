import { Play, Activity, CheckCircle, XCircle } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import './Diagnostics.css';
import { apiUrl, wsUrl } from '../utils/api';

export default function Diagnostics() {
  const [diagnostics, setDiagnostics] = useState([]);
  const [isRunningAll, setIsRunningAll] = useState(false);
  const [runningKey, setRunningKey] = useState('');

  const fetchDiagnostics = async () => {
    try {
      const res = await fetch(apiUrl('/api/diagnostics'));
      const data = await res.json();
      setDiagnostics(data.diagnostics || []);
    } catch (err) {
      console.error('Failed to fetch diagnostics', err);
    }
  };

  useEffect(() => {
    fetchDiagnostics();
  }, []);

  useEffect(() => {
    const ws = new WebSocket(wsUrl('/ws/diagnostics'));
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data?.diagnostics) {
          setDiagnostics(data.diagnostics);
        }
      } catch (err) {
        console.error('Diagnostics stream parse failed', err);
      }
    };

    return () => {
      if (ws.readyState === 1) ws.close();
    };
  }, []);

  const runDiagnostic = async (key) => {
    if (!key) return;
    setRunningKey(key);
    try {
      await fetch(apiUrl('/api/diagnostics/run'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key })
      });
      await fetchDiagnostics();
    } catch (err) {
      console.error('Failed to run diagnostic', err);
    } finally {
      setRunningKey('');
    }
  };

  const runAll = async () => {
    setIsRunningAll(true);
    try {
      await fetch(apiUrl('/api/diagnostics/run'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      await fetchDiagnostics();
    } catch (err) {
      console.error('Failed to run all diagnostics', err);
    } finally {
      setIsRunningAll(false);
    }
  };

  const summary = useMemo(() => {
    const pass = diagnostics.filter((d) => d.status === 'PASS').length;
    const fail = diagnostics.filter((d) => d.status === 'FAIL').length;
    const running = diagnostics.filter((d) => d.status === 'RUNNING').length;
    return { pass, fail, running, total: diagnostics.length };
  }, [diagnostics]);

  const statusClass = (status) => {
    const normalized = String(status || 'READY').toLowerCase();
    return `diag-status status-${normalized}`;
  };

  const StatusIcon = ({ status }) => {
    if (status === 'PASS') return <CheckCircle size={18} className="diag-pass" />;
    if (status === 'FAIL') return <XCircle size={18} className="diag-fail" />;
    return <Activity size={18} className="diag-pending" />;
  };

  return (
    <div className="diagnostics-container">
      <div className="diagnostics-header">
        <div>
          <h2>SYSTEM DIAGNOSTICS</h2>
          <p className="subtitle">Execute unit tests and backend verification</p>
          <p className="diagnostics-summary">PASS: {summary.pass} | FAIL: {summary.fail} | RUNNING: {summary.running} | TOTAL: {summary.total}</p>
        </div>
        <button className="run-all-btn" onClick={runAll} disabled={isRunningAll}>
          <Play size={18} style={{marginRight: '8px'}} /> {isRunningAll ? 'RUNNING...' : 'RUN ALL DIAGNOSTICS'}
        </button>
      </div>

      <div className="diagnostics-grid">
        {diagnostics.map((diag) => (
          <div key={diag.key} className="diag-card">
            <div className="diag-icon"><StatusIcon status={diag.status} /></div>
            <div className="diag-info">
              <h3>{diag.title}</h3>
              <p>{diag.desc}</p>
              <p className="diag-detail">{diag.detail || 'No details yet.'}</p>
            </div>
            <div className="diag-action">
              <span className={statusClass(diag.status)}>{diag.status}</span>
              <button className="test-btn" onClick={() => runDiagnostic(diag.key)} disabled={runningKey === diag.key || isRunningAll}>
                {runningKey === diag.key ? 'RUNNING...' : 'TEST'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
