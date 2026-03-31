import React from 'react';
import { Loader2, CheckCircle, Smartphone, Terminal, Layout } from 'lucide-react';
import './WorkflowStatus.css';

export default function WorkflowStatus({ currentStep, totalSteps, status, steps = [] }) {
  if (!status || status === 'idle') return null;

  return (
    <div className="workflow-status-hud">
      <div className="workflow-header">
        <div className="pulse-icon">
          {status === 'processing' ? <Loader2 className="spin" size={20} /> : <CheckCircle color="#00ff9d" size={20} />}
        </div>
        <div className="workflow-title-group">
          <span className="workflow-label">WOLF ORCHESTRATOR</span>
          <h4 className="workflow-task">{status === 'processing' ? 'Executing Workflow...' : 'Workflow Complete'}</h4>
        </div>
      </div>

      <div className="workflow-steps">
        {steps.map((step, idx) => (
          <div key={idx} className={`workflow-step ${idx < currentStep ? 'completed' : idx === currentStep ? 'active' : 'pending'}`}>
            <div className="step-indicator">
               {idx < currentStep ? <CheckCircle size={14} /> : <div className="dot"></div>}
            </div>
            <span className="step-name">{step}</span>
          </div>
        ))}
      </div>

      <div className="workflow-progress-bg">
        <div 
          className="workflow-progress-fill" 
          style={{ width: `${(currentStep / totalSteps) * 100}%` }}
        ></div>
      </div>
    </div>
  );
}
