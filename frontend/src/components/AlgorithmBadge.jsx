const STYLES = {
  CHACHA: 'border-amber/60 bg-amber/10 text-amber shadow-[0_0_16px_rgba(255,180,0,0.18)]',
  RSA:    'border-rose-400/60 bg-rose-400/10 text-rose-400 shadow-[0_0_16px_rgba(251,113,133,0.18)]',
  // AES and anything else
  DEFAULT:'border-cyan/60 bg-cyan/10 text-cyan shadow-[0_0_16px_rgba(0,229,255,0.18)]'
};

export default function AlgorithmBadge({ algorithm }) {
  const key = (algorithm || '').toUpperCase();
  const cls = STYLES[key] ?? STYLES.DEFAULT;

  return (
    <span className={`inline-flex border px-2 py-1 font-display text-[11px] uppercase ${cls}`}>
      {algorithm || 'UNKNOWN'}
    </span>
  );
}
