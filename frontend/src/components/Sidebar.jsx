import { NavLink } from 'react-router-dom';
import { Home, MessageSquare, Settings, Music, Activity, FileText, CheckSquare, PhoneCall } from 'lucide-react';
import './Sidebar.css';

export default function Sidebar() {
  return (
    <div className="sidebar">
      <div className="logo-section">
        <div className="logo-icon">🐺</div>
        <div className="logo-text">WOLF AI</div>
      </div>
      <nav className="nav-menu">
        <NavLink to="/" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <Home size={20} /> <span>Dashboard</span>
        </NavLink>
        <NavLink to="/chat" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <MessageSquare size={20} /> <span>Chat</span>
        </NavLink>
        <NavLink to="/tasks" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <CheckSquare size={20} /> <span>Tasks</span>
        </NavLink>
        <NavLink to="/media" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <Music size={20} /> <span>Media</span>
        </NavLink>
        <NavLink to="/call-logs" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <PhoneCall size={20} /> <span>Call Logs</span>
        </NavLink>
        <NavLink to="/diagnostics" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <Activity size={20} /> <span>Diagnostics</span>
        </NavLink>
        <NavLink to="/settings" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <Settings size={20} /> <span>Settings</span>
        </NavLink>
      </nav>
    </div>
  );
}
