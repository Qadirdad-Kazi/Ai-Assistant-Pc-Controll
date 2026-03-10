import { Save, RefreshCw } from 'lucide-react';
import './Settings.css';

export default function Settings() {
  return (
    <div className="settings-container">
      <div className="settings-header">
        <h2>SYSTEM CONFIGURATION</h2>
        <div className="save-btn">
          <Save size={18} style={{marginRight: '8px'}}/> APPLY CHANGES
        </div>
      </div>

      <div className="settings-grid">
        <div className="setting-card">
          <h3>Local AI Models</h3>
          <div className="input-group">
            <label>Ollama Endpoint URL</label>
            <input type="text" defaultValue="http://localhost:11434/api" />
          </div>
          <div className="input-group">
            <label>Primary Language Model</label>
            <select defaultValue="llama3.2:3b">
              <option value="llama3.2:3b">Llama 3.2 (3B)</option>
              <option value="qwen2.5:14b">Qwen 2.5 (14B)</option>
              <option value="mistral">Mistral (7B)</option>
            </select>
          </div>
          <div className="input-group">
            <label>Vision Model</label>
            <select defaultValue="llava-phi3">
              <option value="llava-phi3">LLaVA Phi-3</option>
              <option value="llava:13b">LLaVA 13B</option>
            </select>
          </div>
        </div>

        <div className="setting-card">
          <h3>Hardware & Perception</h3>
          <div className="toggle-group">
            <div className="toggle-info">
              <label>Continuous Wake Word Detection</label>
              <p>Listen for 'Wolf' in the background</p>
            </div>
            <label className="switch">
              <input type="checkbox" defaultChecked />
              <span className="slider round"></span>
            </label>
          </div>
          
          <div className="toggle-group">
            <div className="toggle-info">
              <label>Hardware Acceleration (CUDA)</label>
              <p>Use NVIDIA GPU for STT processing</p>
            </div>
            <label className="switch">
              <input type="checkbox" defaultChecked />
              <span className="slider round"></span>
            </label>
          </div>
          
          <div className="toggle-group">
            <div className="toggle-info">
              <label>UI Sound Effects</label>
              <p>Play blips and confirmation sounds</p>
            </div>
            <label className="switch">
              <input type="checkbox" defaultChecked />
              <span className="slider round"></span>
            </label>
          </div>
        </div>

        <div className="setting-card full-width">
          <h3>API Keys & External Integrations</h3>
          <div className="input-group">
            <label>OpenWeatherMap API Key (for weather commands)</label>
            <input type="password" defaultValue="************************" />
          </div>
          <div className="input-group">
            <label>Spotify Client Secret (Optional)</label>
            <input type="password" placeholder="Enter secret to enable Spotify control..." />
          </div>
        </div>
      </div>
    </div>
  );
}
