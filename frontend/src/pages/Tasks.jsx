import { Plus, Play, Edit, Trash2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import './Tasks.css';
import { apiUrl, wsUrl } from '../utils/api';

export default function Tasks() {
  const [tasks, setTasks] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionLog, setExecutionLog] = useState("");
  const [liveEvents, setLiveEvents] = useState([]);
  const [activeExecutionTaskId, setActiveExecutionTaskId] = useState(null);
  
  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newTaskDesc, setNewTaskDesc] = useState("");
  const [editTaskId, setEditTaskId] = useState(null);

  const fetchTasks = async () => {
    try {
      const res = await fetch(apiUrl('/api/tasks'));
      const data = await res.json();
      setTasks(data.tasks || []);
    } catch (e) {
      console.error("Failed to fetch tasks", e);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  useEffect(() => {
    const ws = new WebSocket(wsUrl('/ws/execution'));

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        const incoming = payload.events || [];
        if (incoming.length === 0) return;

        const filtered = activeExecutionTaskId
          ? incoming.filter((evt) => evt.task_id === activeExecutionTaskId)
          : incoming;

        if (filtered.length === 0) return;

        setLiveEvents((prev) => [...prev, ...filtered].slice(-200));

        const lines = filtered.map((evt) => {
          const stepPrefix = evt.step ? `[Step ${evt.step}] ` : '';
          return `[${evt.timestamp}] ${stepPrefix}${evt.type}: ${evt.message}`;
        });

        if (lines.length > 0) {
          setExecutionLog((prev) => {
            const next = prev ? `${prev}\n${lines.join('\n')}` : lines.join('\n');
            const maxChars = 20000;
            return next.length > maxChars ? next.slice(next.length - maxChars) : next;
          });
        }
      } catch (err) {
        console.error('Failed to parse execution event payload', err);
      }
    };

    ws.onerror = (err) => {
      console.error('Execution WebSocket error:', err);
    };

    return () => {
      if (ws.readyState === 1) ws.close();
    };
  }, [activeExecutionTaskId]);

  const handleSaveTask = async (e) => {
    e.preventDefault();
    if (!newTaskTitle.trim() || !newTaskDesc.trim()) return;

    try {
      if (editTaskId) {
        // Edit existing task
        await fetch(apiUrl(`/api/tasks/${editTaskId}`), {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: newTaskTitle, description: newTaskDesc })
        });
      } else {
        // Create new task
        await fetch(apiUrl('/api/tasks'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: newTaskTitle, description: newTaskDesc })
        });
      }
      setIsModalOpen(false);
      setNewTaskTitle("");
      setNewTaskDesc("");
      setEditTaskId(null);
      fetchTasks();
    } catch (e) {
      console.error("Failed to save task", e);
    }
  };

  const openEditModal = (task, e) => {
    e.stopPropagation();
    setEditTaskId(task.id);
    setNewTaskTitle(task.title);
    setNewTaskDesc(task.description);
    setIsModalOpen(true);
  };

  const openCreateModal = () => {
    setEditTaskId(null);
    setNewTaskTitle("");
    setNewTaskDesc("");
    setIsModalOpen(true);
  };

  const handleDeleteTask = async (taskId, e) => {
    e.stopPropagation();
    if (!confirm("Delete this task?")) return;
    
    try {
      await fetch(apiUrl(`/api/tasks/${taskId}`), { method: 'DELETE' });
      if (selectedTask?.id === taskId) {
        setSelectedTask(null);
      }
      fetchTasks();
    } catch (err) {
      console.error("Failed to delete task", err);
    }
  };

  const handleExecuteTask = async () => {
    if (!selectedTask || isExecuting) return;
    
    setIsExecuting(true);
    setActiveExecutionTaskId(selectedTask.id);
    setLiveEvents([]);
    const timeNow = new Date().toLocaleTimeString();
    setExecutionLog(`[${timeNow}] Starting task execution...\n[${timeNow}] Waiting for live execution events...`);
    
    try {
      const res = await fetch(apiUrl(`/api/tasks/${selectedTask.id}/execute`), { method: 'POST' });
      const data = await res.json();
      
      const timeDone = new Date().toLocaleTimeString();
      const newLog = `\n[${timeDone}] Final Response: ${data.message}\n` + 
        (data.data ? JSON.stringify(data.data.result, null, 2) : '');
      
      setExecutionLog(prev => prev + newLog);
      
      // Update tasks list to reflect status changes
      fetchTasks();
    } catch (e) {
      const timeFail = new Date().toLocaleTimeString();
      setExecutionLog(prev => prev + `\n[${timeFail}] Failed to connect to execution engine: ${e.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <>
      <div className="tasks-container">
        <div className="tasks-sidebar">
          <div className="tasks-sidebar-header">
            <h2>TASKS</h2>
            <button className="add-task-btn" onClick={openCreateModal}><Plus size={16}/> ADD TASK</button>
          </div>
          <div className="task-list">
            {tasks.length === 0 ? (
              <div style={{color: '#9ca3af', padding: '1rem', textAlign: 'center'}}>No tasks found. Create one.</div>
            ) : tasks.map(task => (
              <div key={task.id} className={`task-card ${selectedTask?.id === task.id ? 'active' : ''}`} onClick={() => setSelectedTask(task)}>
                <div className="task-card-header">
                  <h4>{task.title}</h4>
                  <span className={`status-badge ${task.status}`}>
                    {task.status === 'completed' ? '✓ Completed' : task.status}
                  </span>
                </div>
                <p className="task-desc">{task.description}</p>
                <div className="task-actions">
                  <button 
                    className="act-btn play" 
                    disabled={task.status === 'completed'}
                    onClick={(e) => { e.stopPropagation(); setSelectedTask(task); setTimeout(handleExecuteTask, 100); }}
                  >
                    <Play size={12}/> Execute
                  </button>
                  <button className="act-btn edit" onClick={(e) => openEditModal(task, e)}><Edit size={12}/> Edit</button>
                  <button className="act-btn delete" onClick={(e) => handleDeleteTask(task.id, e)}><Trash2 size={12}/> Delete</button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="tasks-content">
          {selectedTask ? (
             <div className="task-details-view">
                <h2 className="view-title">Executing: {selectedTask.title}</h2>
                <p className="view-desc">{isExecuting ? "Processing task natively via Python LLM..." : "Ready to execute"}</p>
                
                <div style={{marginBottom: '1rem'}}>
                  <button 
                      className="act-btn play" 
                      style={{padding: '0.5rem 1rem', fontSize: '14px', cursor: isExecuting ? 'wait' : 'pointer'}}
                      disabled={isExecuting}
                      onClick={handleExecuteTask}
                  >
                      <Play size={16}/> {isExecuting ? 'Executing...' : 'Run Task Now'}
                  </button>
                </div>

                <div className="live-events-meta">
                  <span>Live Events: {liveEvents.length}</span>
                  <span>{activeExecutionTaskId ? `Task Stream: ${activeExecutionTaskId}` : 'Task Stream: waiting'}</span>
                </div>

                <div className="execution-log">
                  <div className="log-header">Execution Log:</div>
                  <textarea 
                    className="log-output" 
                    readOnly 
                    value={executionLog || "Awaiting execution..."} 
                  />
                </div>
             </div>
          ) : (
            <div className="empty-selection">
              <h2>Select a task to view details</h2>
              <p>Choose a task from the list to execute, edit, or view details.</p>
            </div>
          )}
        </div>
      </div>

      {isModalOpen && (
        <div className="modal-overlay" onClick={() => setIsModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3 className="modal-title">{editTaskId ? 'Edit Task' : 'Create New Task'}</h3>
            <form onSubmit={handleSaveTask}>
              <div className="modal-group">
                <label>Task Title</label>
                <input 
                  type="text" 
                  value={newTaskTitle} 
                  onChange={(e) => setNewTaskTitle(e.target.value)} 
                  placeholder="e.g., Turn off lights" 
                  autoFocus 
                  required 
                />
              </div>
              <div className="modal-group">
                <label>Task Instruction / AI Prompt</label>
                <textarea 
                  value={newTaskDesc} 
                  onChange={(e) => setNewTaskDesc(e.target.value)} 
                  placeholder="Provide precise instructions for Wolf AI on what to do..."
                  rows={4}
                  required
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="modal-btn cancel" onClick={() => setIsModalOpen(false)}>Cancel</button>
                <button type="submit" className="modal-btn submit">Save Task</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
