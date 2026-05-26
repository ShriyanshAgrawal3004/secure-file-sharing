const levels = [
  {
    key: 'LOW',
    apiValue: '1',
    glow: 'shadow-[0_0_10px_rgba(255,180,0,0.18)]',
    description: 'LOW → AES selected for efficient standard encryption',
    tooltip: 'AES likely. Good for routine documents with low threat exposure.'
  },
  {
    key: 'MEDIUM',
    apiValue: '2',
    glow: 'shadow-[0_0_16px_rgba(255,180,0,0.25)]',
    description: 'MEDIUM → AES selected with elevated handling priority',
    tooltip: 'AES likely. Balanced throughput and stronger storage posture.'
  },
  {
    key: 'HIGH',
    apiValue: '3',
    glow: 'shadow-[0_0_22px_rgba(255,180,0,0.33)]',
    description: 'HIGH → ChaCha20 selected for hardened payload protection',
    tooltip: 'ChaCha20 likely. Better for high-sensitivity encrypted storage.'
  },
  {
    key: 'CRITICAL',
    apiValue: '3',
    glow: 'shadow-[0_0_30px_rgba(255,180,0,0.45)]',
    description: 'CRITICAL → ChaCha20 selected for maximum entropy',
    tooltip: 'ChaCha20 likely. Reserved for maximum sensitivity and warning posture.'
  }
];

export { levels as sensitivityLevels };

export default function SensitivitySelector({ value, onChange }) {
  const active = levels.find((level) => level.key === value) || levels[0];

  return (
    <section className="panel p-5 sm:p-6">
      <div className="mb-5 flex items-center justify-between gap-4">
        <div>
          <p className="terminal-label text-xs">STEP 02 / SENSITIVITY</p>
          <h2 className="font-display mt-2 text-2xl text-text-primary">CLASSIFICATION LEVEL</h2>
        </div>
        <span className="amber-glow font-display text-xs">{active.apiValue.padStart(2, '0')}</span>
      </div>
      <div className="grid grid-cols-2 border border-vault-border sm:grid-cols-4">
        {levels.map((level, index) => {
          const selected = level.key === value;
          return (
            <button
              key={level.key}
              type="button"
              title={level.tooltip}
              onClick={() => onChange(level.key)}
              className={`relative px-3 py-4 font-display text-xs uppercase transition ${
                index > 0 ? 'border-l border-vault-border' : ''
              } ${
                selected
                  ? `bg-amber/15 text-amber ${level.glow}`
                  : 'bg-black/20 text-text-muted hover:bg-cyan/5 hover:text-cyan'
              }`}
            >
              {level.key}
            </button>
          );
        })}
      </div>
      <p className="mt-4 border-l border-amber/50 pl-3 font-display text-xs uppercase text-amber">
        {active.description}
      </p>
    </section>
  );
}
