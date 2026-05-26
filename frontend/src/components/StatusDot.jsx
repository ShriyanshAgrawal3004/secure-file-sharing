export default function StatusDot({ status = 'idle' }) {
  const classes = {
    idle: 'border-vault-border bg-text-muted/20',
    active: 'border-cyan bg-cyan shadow-[0_0_18px_rgba(0,229,255,0.9)] animate-pulse',
    done: 'border-success bg-success shadow-[0_0_16px_rgba(0,230,118,0.75)]',
    error: 'border-danger bg-danger shadow-[0_0_16px_rgba(255,23,68,0.75)]'
  };

  return <span className={`h-3 w-3 border ${classes[status]}`} />;
}
