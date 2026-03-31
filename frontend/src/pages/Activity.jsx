import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Activity as ActivityIcon, CheckCircle, XCircle, Clock, Info } from 'lucide-react';
import './Activity.css';

const Activity = () => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchLogs = async () => {
            try {
                const response = await axios.get('http://localhost:8000/api/action-logs');
                setLogs(response.data.logs || []);
            } catch (error) {
                console.error("Failed to fetch action logs:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchLogs();
        const interval = setInterval(fetchLogs, 5000); // Poll every 5s
        return () => clearInterval(interval);
    }, []);

    const getStatusIcon = (status) => {
        switch (status.toLowerCase()) {
            case 'success': return <CheckCircle size={18} color="#00ff9d" />;
            case 'failed': return <XCircle size={18} color="#ff4b4b" />;
            case 'started': return <Clock size={18} color="#00f3ff" className="spin" />;
            default: return <Info size={18} color="#777" />;
        }
    };

    return (
        <div className="activity-page">
            <header className="page-header">
                <div className="title-group">
                    <ActivityIcon size={32} color="#00f3ff" />
                    <div>
                        <h1>System Activity</h1>
                        <p>Real-time audit trail of all voice-driven automation steps.</p>
                    </div>
                </div>
            </header>

            <div className="activity-container">
                {loading ? (
                    <div className="loading-state">Analyzing logs...</div>
                ) : logs.length === 0 ? (
                    <div className="empty-state">No recent activity detected.</div>
                ) : (
                    <div className="logs-list">
                        {logs.map((log) => (
                            <div key={log.id} className={`log-card ${log.status}`}>
                                <div className="log-icon">{getStatusIcon(log.status)}</div>
                                <div className="log-content">
                                    <div className="log-main">
                                        <span className="log-action">{log.action_name}</span>
                                        <span className="log-time">{new Date(log.timestamp).toLocaleTimeString()}</span>
                                    </div>
                                    <div className="log-details">{log.details}</div>
                                </div>
                                <div className={`log-badge ${log.status}`}>{log.status}</div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Activity;
