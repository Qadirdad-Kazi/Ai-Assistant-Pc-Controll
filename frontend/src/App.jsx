import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Dashboard from './components/Dashboard'
import Sidebar from './components/Sidebar'
import Chat from './pages/Chat'
import Tasks from './pages/Tasks'
import Settings from './pages/Settings'
import Media from './pages/Media'
import CallLogs from './pages/CallLogs'
import Diagnostics from './pages/Diagnostics'
import SystemMonitor from './components/SystemMonitor'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app-container">
        <Sidebar />
        <div className="main-content">
          <SystemMonitor />
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/tasks" element={<Tasks />} />
            <Route path="/media" element={<Media />} />
            <Route path="/call-logs" element={<CallLogs />} />
            <Route path="/diagnostics" element={<Diagnostics />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </div>
      </div>
    </Router>
  )
}

export default App
