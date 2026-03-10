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

  const handleSend = () => {
    if (!inputText.trim()) return;
    
    // Add user message
    const newMsg = { id: Date.now(), sender: 'user', text: inputText };
    setMessages(prev => [...prev, newMsg]);
    setInputText('');
    
    // Simulate AI response
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        sender: 'bot', 
        text: 'Processing request through neural pathways... (API connection pending)' 
      }]);
    }, 1000);
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
