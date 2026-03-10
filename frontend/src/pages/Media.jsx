import { Play, Pause, SkipBack, SkipForward, Volume2, Music as MusicIcon } from 'lucide-react';
import './Media.css';

export default function Media() {
  return (
    <div className="media-container">
      <div className="media-header">
        <h2>NEURAL SONIC PLAYER</h2>
      </div>

      <div className="media-content">
        <div className="player-card">
          <div className="album-art">
            <div className="art-placeholder">
              <MusicIcon size={64} opacity={0.2} />
              <div className="disc-spin"></div>
            </div>
          </div>
          
          <div className="track-info">
            <h3 className="track-title">Cyber City Lights</h3>
            <p className="track-artist">Midnight Protocol</p>
          </div>
          
          <div className="progress-section">
            <div className="time-stamps">
              <span>01:24</span>
              <span>04:15</span>
            </div>
            <div className="progress-bar-bg">
              <div className="progress-bar-fill" style={{width: '35%'}}>
                <div className="progress-thumb"></div>
              </div>
            </div>
          </div>
          
          <div className="controls">
            <button className="ctrl-btn"><SkipBack size={24} /></button>
            <button className="ctrl-btn play"><Play size={32} fill="currentColor" /></button>
            <button className="ctrl-btn"><SkipForward size={24} /></button>
          </div>
          
          <div className="volume-control">
            <Volume2 size={18} color="var(--text-sub)" />
            <div className="vol-bar-bg">
              <div className="vol-bar-fill" style={{width: '70%'}}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
