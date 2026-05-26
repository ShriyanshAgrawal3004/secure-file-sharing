export default function ChainStatusBar() {
  return (
    <div className="relative z-30 border-b border-vault-border bg-vault-panel/80 px-4 py-2 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between font-display text-[11px] uppercase text-text-muted">
        <span>NODE: 127.0.0.1:5000</span>
        <span className="flex items-center gap-2 text-cyan">
          CHAIN: CONNECTED
          <span className="h-2 w-2 bg-success shadow-[0_0_14px_rgba(0,230,118,0.9)]" />
        </span>
      </div>
    </div>
  );
}
