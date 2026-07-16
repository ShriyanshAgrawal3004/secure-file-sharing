import { motion, useMotionValue, useTransform, animate } from 'framer-motion';
import { useEffect, useMemo, useState } from 'react';

// Sensitivity-based security score mapping
// CRITICAL: 90%+ (highest security), HIGH: 75-89%, MEDIUM: 60-74%, LOW: 40-59%
const scoreMap = {
  LOW: 50,           // 40-59%
  MEDIUM: 70,        // 60-74%
  HIGH: 82,          // 75-89%
  CRITICAL: 92       // 90%+
};

function colorForScore(score) {
  if (score >= 85) return '#FF1744';      // Red for CRITICAL/HIGH
  if (score >= 70) return '#FFB400';      // Orange for MEDIUM
  return '#00E5FF';                       // Cyan for LOW
}

export default function SecurityScore({ sensitivity }) {
  const score = scoreMap[sensitivity] || 70;
  const progress = useMotionValue(0);
  const pathLength = useTransform(progress, [0, 100], [0, score / 100]);
  const [count, setCount] = useState(0);
  const color = useMemo(() => colorForScore(score), [score]);

  useEffect(() => {
    const controls = animate(progress, 100, { duration: 1, ease: 'easeOut' });
    const counter = animate(0, score, {
      duration: 1,
      ease: 'easeOut',
      onUpdate: (value) => setCount(Math.round(value))
    });
    return () => {
      controls.stop();
      counter.stop();
    };
  }, [progress, score]);

  return (
    <div className="panel p-6">
      <p className="terminal-label text-xs">SECURITY SCORE</p>
      <div className="mt-5 flex items-center justify-center">
        <div className="relative h-56 w-56">
          <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
            <circle cx="60" cy="60" r="48" fill="none" stroke="rgba(0,229,255,0.13)" strokeWidth="8" />
            <motion.circle
              cx="60"
              cy="60"
              r="48"
              fill="none"
              stroke={color}
              strokeWidth="8"
              strokeLinecap="square"
              pathLength={pathLength}
              strokeDasharray="1"
              filter="drop-shadow(0 0 8px currentColor)"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="font-display text-5xl" style={{ color }}>{count}</span>
            <span className="font-display text-xs text-text-muted">/ 100</span>
          </div>
        </div>
      </div>
    </div>
  );
}
