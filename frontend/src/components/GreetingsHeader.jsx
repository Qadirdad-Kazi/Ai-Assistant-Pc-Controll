import { useState, useEffect } from 'react'
import './GreetingsHeader.css'

export default function GreetingsHeader() {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);


  const formatDate = () => {
    const days = ['SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY'];
    const weekday = days[time.getDay()];
    const month = String(time.getMonth() + 1).padStart(2, '0');
    const day = String(time.getDate()).padStart(2, '0');
    const year = time.getFullYear();
    return `${weekday} | ${month}.${day}.${year}`;
  };

  const formatTime = () => time.toTimeString().split(' ')[0];

  return (
    <div className="header-container">
      <div className="header-text">
      </div>
      <div className="clock-container">
        <div className="clock-text">{formatTime()}</div>
        <div className="date-text">{formatDate()}</div>
      </div>
    </div>
  )
}
