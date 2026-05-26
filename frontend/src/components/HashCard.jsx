import { motion } from 'framer-motion';
import { useState } from 'react';

function truncate(value = '', head = 14, tail = 10) {
  if (!value || value.length <= head + tail + 3) return value;
  return `${value.slice(0, head)}...${value.slice(-tail)}`;
}

export default function HashCard({ label, value, copyable = true }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    if (!copyable || !value) return;
    await navigator.clipboard.writeText(value);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="panel min-h-[138px] p-4">
      <p className="terminal-label text-xs">{label}</p>
      <p className="hash-text mt-4 text-sm leading-6">{truncate(value) || 'PENDING'}</p>
      {copyable && (
        <motion.button
          type="button"
          onClick={copy}
          animate={copied ? { scale: [1, 1.06, 1], color: '#00E5FF' } : { scale: 1 }}
          transition={{ duration: 0.35 }}
          className="cyan-button mt-5 px-3 py-2 text-xs"
        >
          {copied ? 'COPIED ✓' : 'COPY'}
        </motion.button>
      )}
    </div>
  );
}
