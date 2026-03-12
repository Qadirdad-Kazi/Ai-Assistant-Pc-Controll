import { Save, RefreshCw, Phone, Cable, Wifi, Eye, LayoutDashboard } from 'lucide-react';
import { useEffect, useState } from 'react';
import './Settings.css';

export default function Settings() {
  const [form, setForm] = useState({
    theme: 'Dark',
    max_history: 20,
    model_chat: 'llama3.2:3b',
    model_router: './merged_model',
    ollama_url: 'http://localhost:11434',
    tts_engine: 'kokoro',
    tts_voice: 'af_heart',
    wake_word_keyword: 'wolf',
    wake_word_sensitivity: 0.6,
    wake_word_confirmation_count: 1,
    picovoice_enabled: false,
    picovoice_key: '',
    picovoice_ppn_path: 'resources/wakewords/hey_wolf.ppn',
    connection_mode: 'None',
    gsm_port: 'COM3',
    sip_ip: '0.0.0.0',
    bug_watcher_enabled: false,
    hud_enabled: false,
    spotify_client_id: '',
    spotify_client_secret: ''
  });
  const [isSaving, setIsSaving] = useState(false);
  const [notice, setNotice] = useState('');
  const [validation, setValidation] = useState(null);

  const loadSettings = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/settings');
      const data = await res.json();
      const s = data.settings || {};
      setForm({
        theme: s.theme || 'Dark',
        max_history: s.general?.max_history ?? 20,
        model_chat: s.models?.chat || 'llama3.2:3b',
        model_router: s.models?.router || './merged_model',
        ollama_url: s.ollama_url || 'http://localhost:11434',
        tts_engine: s.tts?.engine || 'kokoro',
        tts_voice: s.tts?.voice || 'af_heart',
        wake_word_keyword: s.wake_word?.keyword || 'wolf',
        wake_word_sensitivity: s.wake_word?.sensitivity ?? 0.6,
        wake_word_confirmation_count: s.wake_word?.confirmation_count ?? 1,
        picovoice_enabled: Boolean(s.picovoice?.enabled),
        picovoice_key: s.picovoice?.key || '',
        picovoice_ppn_path: s.picovoice?.ppn_path || 'resources/wakewords/hey_wolf.ppn',
        connection_mode: s.phone?.connection_mode || 'None',
        gsm_port: s.gsm?.port || 'COM3',
        sip_ip: s.sip?.server_ip || '0.0.0.0',
        bug_watcher_enabled: Boolean(s.bug_watcher?.enabled),
        hud_enabled: Boolean(s.hud?.enabled),
        spotify_client_id: s.spotify?.client_id || '',
        spotify_client_secret: s.spotify?.client_secret || '',
      });
    } catch (err) {
      console.error('Failed to load settings', err);
      setNotice('Failed to load settings from backend.');
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const setField = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const applyChanges = async () => {
    setIsSaving(true);
    setNotice('');
    try {
      const payload = {
        settings: {
          theme: form.theme,
          ollama_url: form.ollama_url,
          models: {
            chat: form.model_chat,
            router: form.model_router,
          },
          tts: {
            engine: form.tts_engine,
            voice: form.tts_voice,
          },
          wake_word: {
            keyword: form.wake_word_keyword,
            sensitivity: Number(form.wake_word_sensitivity) || 0.6,
            confirmation_count: Number(form.wake_word_confirmation_count) || 1,
          },
          picovoice: {
            enabled: Boolean(form.picovoice_enabled),
            key: form.picovoice_key,
            ppn_path: form.picovoice_ppn_path,
          },
          general: {
            max_history: Number(form.max_history) || 20,
          },
          phone: {
            connection_mode: form.connection_mode,
          },
          gsm: {
            port: form.gsm_port,
          },
          sip: {
            server_ip: form.sip_ip,
          },
          bug_watcher: {
            enabled: Boolean(form.bug_watcher_enabled),
          },
          hud: {
            enabled: Boolean(form.hud_enabled),
          },
          spotify: {
            client_id: form.spotify_client_id,
            client_secret: form.spotify_client_secret,
          },
        },
      };

      const res = await fetch('http://localhost:8000/api/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      setNotice(data.restart_required ? 'Saved. Some changes require backend restart.' : 'Settings saved successfully.');
    } catch (err) {
      console.error('Failed to save settings', err);
      setNotice('Failed to save settings.');
    } finally {
      setIsSaving(false);
    }
  };

  const resetDefaults = async () => {
    try {
      await fetch('http://localhost:8000/api/settings/reset', { method: 'POST' });
      await loadSettings();
      setNotice('Settings reset to defaults.');
    } catch (err) {
      console.error('Failed to reset settings', err);
      setNotice('Reset failed.');
    }
  };

  const runValidation = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/settings/validate');
      const data = await res.json();
      setValidation(data.checks || null);
    } catch (err) {
      console.error('Validation failed', err);
      setValidation(null);
    }
  };

  return (
    <div className="settings-container">
      <div className="settings-header">
        <h2>SYSTEM CONFIGURATION</h2>
        <div className="settings-actions">
          <button className="refresh-btn" onClick={loadSettings}>
            <RefreshCw size={18} style={{marginRight: '8px'}}/> RELOAD
          </button>
          <button className="refresh-btn" onClick={resetDefaults}>
            RESET DEFAULTS
          </button>
          <button className="save-btn" onClick={applyChanges} disabled={isSaving}>
            <Save size={18} style={{marginRight: '8px'}}/> {isSaving ? 'SAVING...' : 'APPLY CHANGES'}
          </button>
        </div>
      </div>

      {notice && <div className="settings-notice">{notice}</div>}

      <div className="settings-grid">
        <div className="setting-card">
          <h3>Personalization</h3>
          <div className="input-group">
            <label>Application Theme</label>
            <select value={form.theme} onChange={(e) => setField('theme', e.target.value)}>
              <option value="Dark">Dark</option>
              <option value="Light">Light</option>
              <option value="Auto">Auto</option>
            </select>
          </div>
          <div className="input-group">
            <label>Max Chat History</label>
            <input type="number" value={form.max_history} onChange={(e) => setField('max_history', e.target.value)} min={5} max={50} />
          </div>
        </div>

        <div className="setting-card">
          <h3>AI Models</h3>
          <div className="input-group">
            <label>Chat Model (Ollama)</label>
            <select value={form.model_chat} onChange={(e) => setField('model_chat', e.target.value)}>
              <option value="llama3.2:3b">Llama 3.2 (3B)</option>
              <option value="qwen2.5:14b">Qwen 2.5 (14B)</option>
              <option value="mistral">Mistral (7B)</option>
            </select>
          </div>
          <div className="input-group">
            <label>Function Router Model</label>
            <input type="text" value={form.model_router} onChange={(e) => setField('model_router', e.target.value)} />
          </div>
        </div>

        <div className="setting-card">
          <h3>Connection & Audio</h3>
          <div className="input-group">
            <label>Ollama Endpoint URL</label>
            <input type="text" value={form.ollama_url} onChange={(e) => setField('ollama_url', e.target.value)} />
          </div>
          <div className="input-group">
            <label>TTS Engine</label>
            <select value={form.tts_engine} onChange={(e) => setField('tts_engine', e.target.value)}>
              <option value="kokoro">Kokoro (Neural)</option>
              <option value="piper">Piper (Fast)</option>
            </select>
          </div>
          <div className="input-group">
            <label>TTS Voice</label>
            <select value={form.tts_voice} onChange={(e) => setField('tts_voice', e.target.value)}>
              <option value="af_heart">Heart (Female)</option>
              <option value="af_sarah">Sarah (Female)</option>
              <option value="am_adam">Adam (Male)</option>
              <option value="am_michael">Michael (Male)</option>
            </select>
          </div>
          <div className="input-group">
            <label>Wake Word</label>
            <input type="text" value={form.wake_word_keyword} onChange={(e) => setField('wake_word_keyword', e.target.value)} />
          </div>
          <div className="input-group">
            <label>Wake Word Sensitivity (0.1 - 1.0)</label>
            <input type="number" step="0.1" min="0.1" max="1.0" value={form.wake_word_sensitivity} onChange={(e) => setField('wake_word_sensitivity', e.target.value)} />
          </div>
          <div className="input-group">
            <label>Wake Word Confirmation Count</label>
            <input type="number" min="1" max="5" value={form.wake_word_confirmation_count} onChange={(e) => setField('wake_word_confirmation_count', e.target.value)} />
          </div>
          <div className="input-group">
            <label>Picovoice Access Key</label>
            <input type="password" value={form.picovoice_key} onChange={(e) => setField('picovoice_key', e.target.value)} placeholder="Optional" />
          </div>
          <div className="input-group">
            <label>Custom Wakeword PPN Path</label>
            <input type="text" value={form.picovoice_ppn_path} onChange={(e) => setField('picovoice_ppn_path', e.target.value)} />
          </div>
          <div className="input-group">
            <label>Use Picovoice Wake Word Engine</label>
            <select value={form.picovoice_enabled ? 'enabled' : 'disabled'} onChange={(e) => setField('picovoice_enabled', e.target.value === 'enabled')}>
              <option value="disabled">Disabled</option>
              <option value="enabled">Enabled</option>
            </select>
          </div>
          <div className="input-group">
            <label>Spotify Client ID</label>
            <input type="text" value={form.spotify_client_id} onChange={(e) => setField('spotify_client_id', e.target.value)} />
          </div>
          <div className="input-group">
            <label>Spotify Client Secret</label>
            <input type="password" value={form.spotify_client_secret} onChange={(e) => setField('spotify_client_secret', e.target.value)} />
          </div>
          <button className="validate-btn" onClick={runValidation}>VALIDATE CONNECTIONS</button>
          {validation && (
            <div className="validation-box">
              <div>Ollama: {validation.ollama?.ok ? 'OK' : 'FAIL'} ({validation.ollama?.detail})</div>
              <div>Spotify Credentials: {validation.spotify_credentials?.ok ? 'OK' : 'MISSING'} ({validation.spotify_credentials?.detail})</div>
            </div>
          )}
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
                <select value={form.connection_mode} onChange={(e) => setField('connection_mode', e.target.value)}>
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
                <input type="text" value={form.gsm_port} onChange={(e) => setField('gsm_port', e.target.value)} />
              </div>
            </div>

            <div className="gm-item">
              <div className="gm-icon"><Wifi size={20} /></div>
              <div className="gm-info">
                <label>SIP Server IP Address</label>
                <p>IP of your Android Gateway (e.g. 192.168.1.10)</p>
              </div>
              <div className="gm-control">
                <input type="text" value={form.sip_ip} onChange={(e) => setField('sip_ip', e.target.value)} />
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
                  <input type="checkbox" checked={form.bug_watcher_enabled} onChange={(e) => setField('bug_watcher_enabled', e.target.checked)} />
                  <span className="slider round"></span>
                </label>
                <span className="toggle-label">{form.bug_watcher_enabled ? 'On' : 'Off'}</span>
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
                  <input type="checkbox" checked={form.hud_enabled} onChange={(e) => setField('hud_enabled', e.target.checked)} />
                  <span className="slider round"></span>
                </label>
                <span className="toggle-label">{form.hud_enabled ? 'On' : 'Off'}</span>
              </div>
            </div>

          </div>
        </div>

      </div>
    </div>
  );
}
