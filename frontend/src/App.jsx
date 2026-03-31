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
import Analytics from './pages/Analytics'
import SafetyPrompt from './components/SafetyPrompt'
import ClarificationPrompt from './components/ClarificationPrompt'
import CalendarReminder from './components/CalendarReminder'
import WorkflowStatus from './components/WorkflowStatus'
import './workflowStatus.css'
import './App.css'

function App() {
  const [workflow, setWorkflow] = React.useState({
    status: 'idle',
    currentStep: 0,
    totalSteps: 4,
    steps: ["Create Project Folder", "Scaffold HTML/JS", "Launch VS Code", "Tile Workspace"]
  });

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
