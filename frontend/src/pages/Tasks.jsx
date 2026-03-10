import { Plus, Play, Edit, Trash2 } from 'lucide-react';
import { useState } from 'react';
import './Tasks.css';

export default function Tasks() {
  const [tasks, setTasks] = useState([
    { id: 1, title: 'Open Spotify', description: 'Open Spotify and play my workout playlist', status: 'pending' },
    { id: 2, title: 'Lock System', description: 'Lock the computer after 5 minutes', status: 'completed' }
  ]);
  const [selectedTask, setSelectedTask] = useState(null);

  return (
    <div className="tasks-container">
      <div className="tasks-sidebar">
        <div className="tasks-sidebar-header">
          <h2>TASKS</h2>
          <button className="add-task-btn"><Plus size={16}/> ADD TASK</button>
        </div>
        <div className="task-list">
          {tasks.map(task => (
            <div key={task.id} className={`task-card ${selectedTask?.id === task.id ? 'active' : ''}`} onClick={() => setSelectedTask(task)}>
              <div className="task-card-header">
                <h4>{task.title}</h4>
                <span className={`status-badge ${task.status}`}>
                  {task.status === 'completed' ? '✓ Completed' : task.status}
                </span>
              </div>
              <p className="task-desc">{task.description}</p>
              <div className="task-actions">
                <button className="act-btn play" disabled={task.status === 'completed'}><Play size={12}/> Execute</button>
                <button className="act-btn"><Edit size={12}/> Edit</button>
                <button className="act-btn delete"><Trash2 size={12}/> Delete</button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="tasks-content">
        {selectedTask ? (
           <div className="task-details-view">
              <h2 className="view-title">Executing: {selectedTask.title}</h2>
              <p className="view-desc">Processing task...</p>
              
              <div className="execution-log">
                <div className="log-header">Execution Log:</div>
                <textarea 
                  className="log-output" 
                  readOnly 
                  defaultValue={`[10:15:00] Starting task execution...\n[10:15:01] Routed to: SystemControl.execute\n[10:15:02] ✓ Task completed successfully`} 
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
  );
}
