export default function AlgorithmBadge({ algorithm }) {
  const isChaCha = algorithm === 'CHACHA';

  return (
    <span
      className={`inline-flex border px-2 py-1 font-display text-[11px] uppercase ${
        isChaCha
          ? 'border-amber/60 bg-amber/10 text-amber shadow-[0_0_16px_rgba(255,180,0,0.18)]'
          : 'border-cyan/60 bg-cyan/10 text-cyan shadow-[0_0_16px_rgba(0,229,255,0.18)]'
      }`}
    >
      {algorithm}
    </span>
  );
}
