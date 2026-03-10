import { useState, useEffect } from 'react'
import './GreetingsHeader.css'

export default function GreetingsHeader() {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  const getGreeting = () => {
    const hour = time.getHours();
    if (hour >= 5 && hour < 12) return "MORNING ADVISOR";
    if (hour >= 12 && hour < 18) return "AFTERNOON PROTOCOL";
    return "EVENING SECURITY";
  };

  const formatDate = () => {
    const options = { year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'long' };
    return time.toLocaleDateString('en-US', options).toUpperCase().replace(/,/g, ' |').replace(/\//g, '.');
  };

  const formatTime = () => time.toTimeString().split(' ')[0];

  return (
    <div className="header-container">
      <div className="header-text">
        <div className="status-text">// {getGreeting()} ACTIVE</div>
        <div className="main-title">COMMANDER</div>
        <div className="date-text">{formatDate()}</div>
      </div>
      <div className="clock-text">{formatTime()}</div>
    </div>
  )
}
