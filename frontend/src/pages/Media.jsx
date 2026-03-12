import { Play, Pause, SkipBack, SkipForward, Volume2, Music as MusicIcon } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import Visualizer from '../components/Visualizer';
import './Media.css';

export default function Media() {
  const audioRef = useRef(null);
  const [query, setQuery] = useState('');
  const [audioProgressSec, setAudioProgressSec] = useState(0);
  const [audioDurationSec, setAudioDurationSec] = useState(0);
  const [state, setState] = useState({
    isPlaying: false,
    service: 'auto',
    source: 'none',
    trackTitle: 'Idle',
    trackArtist: 'Wolf AI',
    durationSec: 0,
    positionSec: 0,
    volume: 70,
    streamUrl: ''
  });

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/media');
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data?.state) {
          setState(data.state);
        }
      } catch (err) {
        console.error('Failed to parse media state payload', err);
      }
    };

    ws.onerror = (err) => {
      console.error('Media WebSocket error:', err);
    };

    return () => {
      if (ws.readyState === 1) ws.close();
    };
  }, []);

  useEffect(() => {
    if (!audioRef.current) return;

    const element = audioRef.current;
    const src = state.streamUrl
      ? (state.streamUrl.startsWith('http') ? state.streamUrl : `http://localhost:8000${state.streamUrl}`)
      : '';

    if (src && element.src !== src) {
      element.src = src;
      element.load();
    }

    if (src) {
      if (state.isPlaying) {
        element.play().catch(() => {
          // Browser autoplay policies may block without user gesture.
        });
      } else {
        element.pause();
      }
    }
  }, [state.streamUrl, state.isPlaying]);

  const progressPercent = useMemo(() => {
    const duration = audioDurationSec > 0 ? audioDurationSec : state.durationSec;
    const position = audioDurationSec > 0 ? audioProgressSec : state.positionSec;
    if (!duration || duration <= 0) return 0;
    return Math.min(100, Math.max(0, (position / duration) * 100));
  }, [state.durationSec, state.positionSec, audioDurationSec, audioProgressSec]);

  const fmt = (sec) => {
    const safe = Math.max(0, Math.floor(sec || 0));
    const m = Math.floor(safe / 60);
    const s = safe % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  };

  const sendControl = async (action, extra = {}) => {
    try {
      await fetch('http://localhost:8000/api/media/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, ...extra })
      });
    } catch (err) {
      console.error('Media control request failed', err);
    }
  };

  const onVolumeChange = (e) => {
    const volume = Number(e.target.value);
    sendControl('set_volume', { volume });
    if (audioRef.current) {
      audioRef.current.volume = volume / 100;
    }
  };

  const playFromQuery = () => {
    const effectiveQuery = query.trim() || state.trackTitle || 'lofi beats';
    sendControl('play', { query: effectiveQuery, service: 'auto' });
  };

  const shownPos = audioDurationSec > 0 ? audioProgressSec : state.positionSec;
  const shownDuration = audioDurationSec > 0 ? audioDurationSec : state.durationSec;

  return (
    <div className="media-container">
      <div className="media-header">
        <h2>NEURAL SONIC PLAYER</h2>
        <p className="media-subtitle">LIVE BACKEND STREAM · SOURCE: {String(state.source || 'none').toUpperCase()}</p>
      </div>

      <div className="media-content">
        <div className="player-card">
          <div className="album-art">
            <div className="art-placeholder">
              <MusicIcon size={64} opacity={0.2} />
              <div className="disc-spin"></div>
            </div>
            <Visualizer audioRef={audioRef} isPlaying={state.isPlaying} />
          </div>
          
          <div className="track-info">
            <h3 className="track-title">{state.trackTitle || 'Idle'}</h3>
            <p className="track-artist">{state.trackArtist || 'Wolf AI'}</p>
          </div>

          <div className="query-row">
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search song or artist (auto: Spotify -> Local -> YouTube)"
              className="query-input"
            />
            <button className="query-play-btn" onClick={playFromQuery}>Play</button>
          </div>
          
          <div className="progress-section">
            <div className="time-stamps">
              <span>{fmt(shownPos)}</span>
              <span>{fmt(shownDuration)}</span>
            </div>
            <div className="progress-bar-bg">
              <div className="progress-bar-fill" style={{width: `${progressPercent}%`}}>
                <div className="progress-thumb"></div>
              </div>
            </div>
          </div>
          
          <div className="controls">
            <button className="ctrl-btn" onClick={() => sendControl('previous')}><SkipBack size={24} /></button>
            <button className="ctrl-btn play" onClick={() => sendControl(state.isPlaying ? 'pause' : 'play', state.isPlaying ? {} : { query: state.trackTitle || query || 'lofi beats', service: 'auto' })}>
              {state.isPlaying ? <Pause size={32} fill="currentColor" /> : <Play size={32} fill="currentColor" />}
            </button>
            <button className="ctrl-btn" onClick={() => sendControl('next')}><SkipForward size={24} /></button>
          </div>
          
          <div className="volume-control">
            <Volume2 size={18} color="var(--text-sub)" />
            <div className="vol-bar-bg">
              <div className="vol-bar-fill" style={{width: `${state.volume || 0}%`}}></div>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={state.volume || 0}
              onChange={onVolumeChange}
              className="vol-slider"
            />
          </div>

          <audio
            ref={audioRef}
            className="native-audio"
            onTimeUpdate={(e) => setAudioProgressSec(e.currentTarget.currentTime || 0)}
            onLoadedMetadata={(e) => setAudioDurationSec(e.currentTarget.duration || 0)}
            onEnded={() => sendControl('pause')}
            controls
          />
        </div>
      </div>
    </div>
  );
}
