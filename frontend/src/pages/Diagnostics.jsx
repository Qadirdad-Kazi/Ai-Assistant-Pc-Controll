import { Play, Activity, CheckCircle, XCircle } from 'lucide-react';
import './Diagnostics.css';

const diagnostics = [
  { id: 1, title: 'Router API', desc: 'Test local LLM and Ollama bindings', status: 'READY' },
  { id: 2, title: 'Local Database', desc: 'Verify SQLite read/write access', status: 'READY' },
  { id: 3, title: 'TTS Engine', desc: 'Check Piper speech synthesis binaries', status: 'READY' },
  { id: 4, title: 'STT Engine', desc: 'Validate Transcription vs Porcupine engine', status: 'READY' },
  { id: 5, title: 'PC Control', desc: 'Check screen control and system permissions', status: 'READY' },
  { id: 6, title: 'Phone Gateway', desc: 'Validate SIP/GSM hardware connection', status: 'READY' },
  { id: 7, title: 'OCR Vision', desc: 'Detect Tesseract engine for Bug Watcher', status: 'READY' }
];

export default function Diagnostics() {
  return (
    <div className="diagnostics-container">
      <div className="diagnostics-header">
        <div>
          <h2>SYSTEM DIAGNOSTICS</h2>
          <p className="subtitle">Execute unit tests and backend verification</p>
        </div>
        <button className="run-all-btn">
          <Play size={18} style={{marginRight: '8px'}} /> RUN ALL DIAGNOSTICS
        </button>
      </div>

      <div className="diagnostics-grid">
        {diagnostics.map((diag) => (
          <div key={diag.id} className="diag-card">
            <div className="diag-icon"><Activity size={24} /></div>
            <div className="diag-info">
              <h3>{diag.title}</h3>
              <p>{diag.desc}</p>
            </div>
            <div className="diag-action">
              <span className="diag-status">{diag.status}</span>
              <button className="test-btn">TEST</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
