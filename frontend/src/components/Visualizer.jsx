import React, { useEffect, useRef } from 'react';
import './Visualizer.css';

const Visualizer = ({ audioRef, isPlaying }) => {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const sourceRef = useRef(null);

  useEffect(() => {
    if (!audioRef.current || !isPlaying) {
        if (animationRef.current) cancelAnimationFrame(animationRef.current);
        return;
    }

    const initAudio = () => {
      try {
        if (!audioContextRef.current) {
          audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
        }

        if (!analyserRef.current) {
          analyserRef.current = audioContextRef.current.createAnalyser();
          analyserRef.current.fftSize = 256;
        }

        if (!sourceRef.current) {
          sourceRef.current = audioContextRef.current.createMediaElementSource(audioRef.current);
          sourceRef.current.connect(analyserRef.current);
          analyserRef.current.connect(audioContextRef.current.destination);
        }

        if (audioContextRef.current.state === 'suspended') {
          audioContextRef.current.resume();
        }
      } catch (err) {
        console.error('Visualizer initialization failed', err);
      }
    };

    initAudio();

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      animationRef.current = requestAnimationFrame(draw);
      analyserRef.current.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const barWidth = (canvas.width / bufferLength) * 2.5;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height * 0.8;
        
        // Create futuristic gradient
        const gradient = ctx.createLinearGradient(0, canvas.height, 0, canvas.height - barHeight);
        gradient.addColorStop(0, '#ff007b');
        gradient.addColorStop(1, '#4cc9f0');

        ctx.fillStyle = gradient;
        
        // Draw with some glow
        ctx.shadowBlur = 10;
        ctx.shadowColor = '#ff007b';
        
        // Rounded bars for "Sonic" feel
        const radius = barWidth / 2;
        ctx.beginPath();
        ctx.roundRect(x, canvas.height - barHeight, barWidth - 2, barHeight, [radius, radius, 0, 0]);
        ctx.fill();

        x += barWidth + 1;
      }
    };

    draw();

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [audioRef, isPlaying]);

  return (
    <div className="visualizer-wrapper">
      <canvas ref={canvasRef} width={300} height={100} className="frequency-canvas" />
      <div className="visualizer-overlay"></div>
    </div>
  );
};

export default Visualizer;
