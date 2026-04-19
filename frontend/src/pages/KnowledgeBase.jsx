import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Brain, Zap, Trash2, Shield, Calendar, Terminal } from 'lucide-react';
import './KnowledgeBase.css';
import { apiUrl } from '../utils/api';

const KnowledgeBase = () => {
    const [heuristics, setHeuristics] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchHeuristics();
    }, []);

    const fetchHeuristics = async () => {
        try {
            const response = await axios.get(apiUrl('/api/knowledge'));
            setHeuristics(response.data.heuristics || []);
        } catch (error) {
            console.error("Failed to fetch knowledge base:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id) => {
        if (window.confirm("Are you sure you want Wolf to forget this learned behavior?")) {
            // In a real app, you'd call a delete endpoint here. 
            // For now, we'll just filter it locally for the UI.
            setHeuristics(heuristics.filter(h => h.id !== id));
        }
    };

    const parseSteps = (planJson) => {
        try {
            const plan = JSON.parse(planJson);
            return plan.length;
        } catch {
            return 0;
        }
    };

    return (
        <div className="knowledge-base-page">
            <header className="page-header">
                <div className="title-group">
                    <div className="brain-container">
                        <Brain size={36} color="#00f3ff" />
                        <div className="neural-pulse"></div>
                    </div>
                    <div>
                        <h1>Synaptic Knowledge Base</h1>
                        <p>Managing Wolf AI's autonomously learned heuristics and custom workflows.</p>
                    </div>
                </div>
            </header>

            <div className="knowledge-grid">
                {loading ? (
                    <div className="loading-state">Accessing neural memory...</div>
                ) : heuristics.length === 0 ? (
                    <div className="empty-state">
                        <Shield size={48} color="rgba(255,255,255,0.1)" />
                        <h3>Memory is Clean</h3>
                        <p>Wolf hasn't needed to learn any custom corrections yet. It will adapt as you give guidance.</p>
                    </div>
                ) : (
                    heuristics.map((h) => (
                        <div key={h.id} className="heuristic-card">
                            <div className="card-header">
                                <div className="query-pill">"{h.query}"</div>
                                <button className="delete-btn" onClick={() => handleDelete(h.id)}>
                                    <Trash2 size={16} />
                                </button>
                            </div>
                            
                            <div className="card-stats">
                                <div className="stat-item">
                                    <Terminal size={14} />
                                    <span>{parseSteps(h.learned_plan)} Optimized Steps</span>
                                </div>
                                <div className="stat-item">
                                    <Zap size={14} color="#00ff9d" />
                                    <span>Used {h.success_count} times</span>
                                </div>
                                <div className="stat-item">
                                    <Calendar size={14} />
                                    <span>Learned: {new Date(h.timestamp).toLocaleDateString()}</span>
                                </div>
                            </div>

                            <div className="execution-preview">
                                <div className="preview-label">ACTIVE HEURISTIC</div>
                                <div className="preview-bar"></div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default KnowledgeBase;
