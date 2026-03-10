import { useState, useRef, useEffect } from 'react';
import { Send, User, Bot } from 'lucide-react';
import './Chat.css';

export default function Chat() {
  const [messages, setMessages] = useState([
    { id: 1, sender: 'bot', text: 'System initialized. How can I assist you today, Commander?' }
  ]);
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/chat');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.messages && data.messages.length > 0) {
        // Map backend format to frontend format
        const formatted = data.messages.map((m, i) => ({
          id: i,
          sender: m.role === 'user' ? 'user' : 'bot',
          text: m.content
        }));
        setMessages(formatted);
      }
    };

    return () => {
      if (ws.readyState === 1) ws.close();
    };
  }, []);

  const handleSend = async () => {
    if (!inputText.trim()) return;
    
    const textToSend = inputText;
    setInputText('');
    
    // Optimistically update the UI instantly so there's no lag
    setMessages(prev => [
      ...prev, 
      { id: Date.now(), sender: 'user', text: textToSend },
      { id: Date.now() + 1, sender: 'bot', text: 'Processing...' }
    ]);
    
    try {
      await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: textToSend })
      });
    } catch (e) {
      console.error("Failed to send message:", e);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>COMMUNICATIONS LINK</h2>
        <div className="status-indicator">
          <span className="pulse-dot"></span> SECURE CHANNEL
        </div>
      </div>
      
      <div className="messages-area">
        {messages.map(msg => (
          <div key={msg.id} className={`message-wrapper ${msg.sender === 'user' ? 'user' : 'bot'}`}>
            <div className="message-bubble">
              <div className="message-avatar">
                {msg.sender === 'user' ? <User size={18} /> : <span className="bot-icon">🐺</span>}
              </div>
              <div className="message-text">{msg.text}</div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="input-area">
        <input 
          type="text" 
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Transmit message..."
          className="chat-input"
        />
        <button onClick={handleSend} className="send-btn">
          <Send size={20} />
        </button>
      </div>
    </div>
  );
}
