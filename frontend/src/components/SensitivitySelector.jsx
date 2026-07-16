// apiValue maps directly to the backend sensitivity int (0–3).
// The ML model uses file features + sensitivity to predict the algorithm;
// descriptions below reflect the model's learned tendencies, not hard rules.
const levels = [
  {
    key: 'LOW',
    apiValue: '0',
    glow: 'shadow-[0_0_10px_rgba(255,180,0,0.18)]',
    description: 'LOW → ML model predicts ChaCha20 for speed-priority storage',
    tooltip: 'ChaCha20 likely. Optimised for throughput on low-risk payloads.'
  },
  {
    key: 'MEDIUM',
    apiValue: '1',
    glow: 'shadow-[0_0_16px_rgba(255,180,0,0.25)]',
    description: 'MEDIUM → ML model selects AES or ChaCha20 based on file entropy',
    tooltip: 'AES or ChaCha20. Model weighs entropy, compressibility, and size.'
  },
  {
    key: 'HIGH',
    apiValue: '2',
    glow: 'shadow-[0_0_22px_rgba(255,180,0,0.33)]',
    description: 'HIGH → ML model predicts AES for strong symmetric encryption',
    tooltip: 'AES likely. Elevated sensitivity shifts model toward AES-256.'
  },
  {
    key: 'CRITICAL',
    apiValue: '3',
    glow: 'shadow-[0_0_30px_rgba(255,180,0,0.45)]',
    description: 'CRITICAL → RSA enforced for asymmetric key-based security',
    tooltip: 'RSA guaranteed. Critical sensitivity always triggers asymmetric encryption.'
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
      <p className="mt-3 border border-vault-border bg-black/30 px-3 py-2 font-display text-[11px] text-cyan">
        ML <span className="text-text-muted">▸</span> {active.description.replace(/^[A-Z]+ → /, '')}
      </p>
    </section>
  );
}
