import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Dashboard from './components/Dashboard'
import Sidebar from './components/Sidebar'
import Chat from './pages/Chat'
import Tasks from './pages/Tasks'
import Settings from './pages/Settings'
import Media from './pages/Media'
import CallLogs from './pages/CallLogs'
import Diagnostics from './pages/Diagnostics'
import Privacy from './pages/Privacy'
import ActivityPage from './pages/Activity'
import KnowledgeBase from './pages/KnowledgeBase'
import './pages/KnowledgeBase.css'
import Analytics from './pages/Analytics'
import SafetyPrompt from './components/SafetyPrompt'
import ClarificationPrompt from './components/ClarificationPrompt'
import CalendarReminder from './components/CalendarReminder'
import WorkflowStatus from './components/WorkflowStatus'
import './App.css'

function App() {
  const [workflow, setWorkflow] = useState(null);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/status');
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.active_workflow) {
          setWorkflow(data.active_workflow);
        } else {
          setWorkflow(null);
        }
      } catch (err) {
        console.error("Status WS error in App.jsx", err);
      }
    };
    return () => ws.close();
  }, []);

  return (
    <Router>
      <div className="app-container">
        <Sidebar />
        <div className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/tasks" element={<Tasks />} />
            <Route path="/media" element={<Media />} />
            <Route path="/call-logs" element={<CallLogs />} />
            <Route path="/activity" element={<ActivityPage />} />
            <Route path="/knowledge" element={<KnowledgeBase />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/diagnostics" element={<Diagnostics />} />
            <Route path="/privacy" element={<Privacy />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </div>
        <WorkflowStatus {...workflow} />
        <CalendarReminder />
        <SafetyPrompt />
        <ClarificationPrompt />
        <CalendarReminder />
      </div>
    </Router>
  )
}

export default App
