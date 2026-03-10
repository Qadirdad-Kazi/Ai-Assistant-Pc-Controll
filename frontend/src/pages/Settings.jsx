import { Save, RefreshCw, Phone, Cable, Wifi, Eye, LayoutDashboard } from 'lucide-react';
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
          <h3>Personalization</h3>
          <div className="input-group">
            <label>Application Theme</label>
            <select defaultValue="Dark">
              <option value="Dark">Dark</option>
              <option value="Light">Light</option>
              <option value="Auto">Auto</option>
            </select>
          </div>
          <div className="input-group">
            <label>Max Chat History</label>
            <input type="number" defaultValue={20} min={5} max={50} />
          </div>
        </div>

        <div className="setting-card">
          <h3>AI Models</h3>
          <div className="input-group">
            <label>Chat Model (Ollama)</label>
            <select defaultValue="llama3.2:3b">
              <option value="llama3.2:3b">Llama 3.2 (3B)</option>
              <option value="qwen2.5:14b">Qwen 2.5 (14B)</option>
              <option value="mistral">Mistral (7B)</option>
            </select>
          </div>
          <div className="input-group">
            <label>Function Router Model</label>
            <input type="text" readOnly defaultValue="Local FunctionGemma model at: ./models/gemma" />
          </div>
        </div>

        <div className="setting-card">
          <h3>Connection & Audio</h3>
          <div className="input-group">
            <label>Ollama Endpoint URL</label>
            <input type="text" defaultValue="http://localhost:11434/api" />
          </div>
          <div className="input-group">
            <label>TTS Voice</label>
            <select defaultValue="Male (Northern)">
              <option value="Male (Northern)">Male (Northern)</option>
              <option value="Female (Alba)">Female (Alba)</option>
            </select>
          </div>
        </div>

        <div className="setting-card full-width god-mode-section">
          <h3 className="gm-title">GOD-MODE INTEGRATIONS</h3>
          <div className="gm-list">

            <div className="gm-item">
              <div className="gm-icon"><Phone size={20} /></div>
              <div className="gm-info">
                <label>Receptionist Connection Mode</label>
                <p>Choose between Physical GSM Hardware or Wireless SIP/VoIP over Wi-Fi</p>
              </div>
              <div className="gm-control">
                <select defaultValue="None">
                  <option value="None">None</option>
                  <option value="GSM Hardware (Serial)">GSM Hardware (Serial)</option>
                  <option value="Wi-Fi Softphone (SIP)">Wi-Fi Softphone (SIP)</option>
                </select>
              </div>
            </div>

            <div className="gm-item">
              <div className="gm-icon"><Cable size={20} /></div>
              <div className="gm-info">
                <label>GSM Gateway COM Port</label>
                <p>Physical USB Serial port for SIM800L (e.g. COM3)</p>
              </div>
              <div className="gm-control">
                <input type="text" defaultValue="COM3" />
              </div>
            </div>

            <div className="gm-item">
              <div className="gm-icon"><Wifi size={20} /></div>
              <div className="gm-info">
                <label>SIP Server IP Address</label>
                <p>IP of your Android Gateway (e.g. 192.168.1.10)</p>
              </div>
              <div className="gm-control">
                <input type="text" defaultValue="0.0.0.0" />
              </div>
            </div>

            <div className="gm-item">
              <div className="gm-icon"><Eye size={20} /></div>
              <div className="gm-info">
                <label>Proactive Bug Watcher</label>
                <p>Background OCR thread that scans screen for crashes</p>
              </div>
              <div className="gm-control toggle-control">
                <label className="switch">
                  <input type="checkbox" />
                  <span className="slider round"></span>
                </label>
                <span className="toggle-label">Off</span>
              </div>
            </div>

            <div className="gm-item">
              <div className="gm-icon"><LayoutDashboard size={20} /></div>
              <div className="gm-info">
                <label>Transparent Desktop HUD</label>
                <p>Enable the ghostly overlay for proactive alerts</p>
              </div>
              <div className="gm-control toggle-control">
                <label className="switch">
                  <input type="checkbox" />
                  <span className="slider round"></span>
                </label>
                <span className="toggle-label">Off</span>
              </div>
            </div>

          </div>
        </div>

      </div>
    </div>
  );
}
