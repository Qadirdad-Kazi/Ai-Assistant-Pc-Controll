import React, { useEffect, useState } from 'react';
import { TrendingUp, Users, CheckCircle, PieChart, DollarSign, Activity } from 'lucide-react';
import './Analytics.css';

export default function Analytics() {
  const [data, setData] = useState({
    metrics: { pipeline_value: 0, total_calls: 0, total_tasks: 0, success_rate: 0 },
    top_clients: [],
    heatmap: []
  });
  const [isLoading, setIsLoading] = useState(true);

  const fetchData = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/analytics/summary');
      const json = await res.json();
      setData(json);
    } catch (e) {
      console.error('Failed to fetch analytics', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (isLoading) return <div className="analytics-loading">Calculating Business Intelligence...</div>;

  const noData = !data.metrics || data.metrics.total_calls === 0;

  return (
    <div className="analytics-container">
      <div className="analytics-header">
        <div>
          <h2>STRATEGY DASHBOARD</h2>
          <p className="subtitle">EXECUTIVE KPI & PIPELINE ANALYSIS</p>
        </div>
        <button className="refresh-btn" onClick={fetchData}>
          Update Metrics
        </button>
      </div>

      {noData ? (
        <div className="no-data-overlay">
          <div className="no-data-content">
            <TrendingUp size={48} className="no-data-icon" />
            <h3>No Strategic Data Detected</h3>
            <p>Wolf is awaiting intercepted calls to begin generating pipeline intelligence.</p>
            <button className="refresh-btn" onClick={fetchData}>Synchronize Now</button>
          </div>
        </div>
      ) : (
        <>
          {/* Metric Cards */}
          <div className="metrics-grid">
            <div className="metric-card gold">
              <div className="metric-icon"><DollarSign size={24} /></div>
              <div className="metric-details">
                <span className="label">Pipeline Value</span>
                <h3 className="value">${(data.metrics?.pipeline_value || 0).toLocaleString()}</h3>
              </div>
            </div>
            <div className="metric-card cyan">
              <div className="metric-icon"><Activity size={24} /></div>
              <div className="metric-details">
                <span className="label">Total Intercepts</span>
                <h3 className="value">{data.metrics.total_calls}</h3>
              </div>
            </div>
            <div className="metric-card pink">
              <div className="metric-icon"><TrendingUp size={24} /></div>
              <div className="metric-details">
                <span className="label">Action Items</span>
                <h3 className="value">{data.metrics.total_tasks}</h3>
              </div>
            </div>
            <div className="metric-card green">
              <div className="metric-icon"><CheckCircle size={24} /></div>
              <div className="metric-details">
                <span className="label">Success Rate</span>
                <h3 className="value">{data.metrics.success_rate}%</h3>
              </div>
            </div>
          </div>

          <div className="analytics-grid-secondary">
            {/* Top Clients Leaderboard */}
            <div className="analytics-panel">
              <div className="panel-header">
                <Users size={18} />
                <h4>TOP CLIENT ENGAGEMENT</h4>
              </div>
              <table className="leaderboard-table">
                <thead>
                  <tr>
                    <th>CLIENT</th>
                    <th>CALLS</th>
                    <th>VALUE</th>
                    <th>SENTIMENT</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.top_clients || []).map((client, i) => (
                    <tr key={i}>
                      <td className="client-name">{client.caller_id}</td>
                      <td>{(client.call_count || 0).toLocaleString()}</td>
                      <td className="value-cell">${(client.total_value || 0).toLocaleString()}</td>
                      <td>
                        <div className="sentiment-bar-bg">
                          <div className="sentiment-bar-fill" style={{ width: `${(client.avg_sentiment || 0) * 10}%` }}></div>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pipeline Heatmap */}
            <div className="analytics-panel">
              <div className="panel-header">
                <PieChart size={18} />
                <h4>PIPELINE HEALTH (BY MOOD)</h4>
              </div>
              <div className="heatmap-list">
                {(data.heatmap || []).map((item, i) => (
                  <div key={i} className="heatmap-item">
                    <div className="heatmap-label-row">
                      <span className="mood-label">{item.mood}</span>
                      <span className="mood-value">${(item.value || 0).toLocaleString()}</span>
                    </div>
                    <div className="heatmap-progress-bg">
                      <div
                        className={`heatmap-progress-bar ${item.mood?.toLowerCase() || ''}`}
                        style={{ width: `${((item.value || 0) / (data.metrics?.pipeline_value || 1)) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
