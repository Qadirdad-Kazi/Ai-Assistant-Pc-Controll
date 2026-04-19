import { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, ChevronDown, ChevronUp, Terminal, Zap } from 'lucide-react';
import './Chat.css';
import { apiUrl, wsUrl } from '../utils/api';

export default function Chat() {
  const [messages, setMessages] = useState([
    { id: 1, sender: 'bot', text: 'System initialized. How can I assist you today, Commander?' }
  ]);
  const [inputText, setInputText] = useState('');
  const [executionEvents, setExecutionEvents] = useState([]);
  const messagesEndRef = useRef(null);
  const [showThinking, setShowThinking] = useState({});

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Main Chat WebSocket
    const chatWs = new WebSocket(wsUrl('/ws/chat'));
    chatWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.messages) {
        setMessages(data.messages.map((m, i) => ({
          id: i,
          sender: m.role === 'user' ? 'user' : 'bot',
          text: m.content,
          metadata: m.metadata || {}
        })));
      }
    };

    // Execution Events WebSocket
    const execWs = new WebSocket(wsUrl('/ws/execution'));
    execWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.events) {
        setExecutionEvents(prev => [...prev, ...data.events].slice(-50));
      }
    };

    return () => {
      chatWs.close();
      execWs.close();
    };
  }, []);

  const handleSend = async () => {
    if (!inputText.trim()) return;
    const textToSend = inputText;
    setInputText('');
    
    // Optimistic UI
    setMessages(prev => [
      ...prev, 
      { id: Date.now(), sender: 'user', text: textToSend },
      { id: Date.now() + 1, sender: 'bot', text: 'Thinking...' }
    ]);
    
    try {
      await fetch(apiUrl('/api/chat'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: textToSend })
      });
    } catch (e) {
      console.error("Failed to send message:", e);
    }
  };

  const toggleThinking = (id) => {
    setShowThinking(prev => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="header-title">
          <Zap size={20} className="header-icon" />
          <h2>COMMUNICATIONS LINK</h2>
        </div>
        <div className="status-indicator">
          <span className="pulse-dot"></span> SECURE CHANNEL
        </div>
      </div>
      
      <div className="chat-layout">
        <div className="messages-area">
          {messages.map((msg) => (
            <div key={msg.id} className={`message-wrapper ${msg.sender === 'user' ? 'user' : 'bot'}`}>
              <div className="message-bubble">
                <div className="message-avatar">
                  {msg.sender === 'user' ? <User size={18} /> : <span className="bot-icon">🐺</span>}
                </div>
                <div className="message-content">
                  <div className="message-text">{msg.text}</div>
                  
                  {msg.metadata?.stages && (
                    <div className="thinking-container">
                      <button 
                        className="thinking-toggle"
                        onClick={() => toggleThinking(msg.id)}
                      >
                        {showThinking[msg.id] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                        Reasoning Process ({msg.metadata.stages.length} stages)
                      </button>
                      
                      {showThinking[msg.id] && (
                        <div className="thinking-stages">
                          {msg.metadata.stages.map((stage, idx) => (
                            <div key={idx} className="thinking-stage">
                              <div className="stage-name">{stage.name}</div>
                              <div className="stage-content">{stage.content}</div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="execution-sidebar">
          <div className="sidebar-header">
            <Terminal size={14} /> TOOL EXECUTION LOG
          </div>
          <div className="events-list">
            {executionEvents.length === 0 && <div className="no-events">Waiting for actions...</div>}
            {executionEvents.map((ev) => (
              <div key={ev.id} className={`event-item ${ev.type}`}>
                <span className="event-time">{new Date(ev.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})}</span>
                <span className="event-msg">{ev.message}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      <div className="input-area">
        <input 
          type="text" 
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Transmit command to Wolf AI..."
          className="chat-input"
        />
        <button onClick={handleSend} className="send-btn">
          <Send size={20} />
        </button>
      </div>
    </div>
  );
}
