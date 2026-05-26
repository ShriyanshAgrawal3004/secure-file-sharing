import { motion } from 'framer-motion';
import StatusDot from './StatusDot.jsx';

function truncate(value = '') {
  if (!value) return '';
  if (value.length <= 18) return value;
  return `${value.slice(0, 10)}...${value.slice(-8)}`;
}

export default function EncryptionStepper({ stage, elapsed, result, error }) {
  const stages = [
    {
      id: 1,
      title: 'ENCRYPTING FILE',
      detail: result?.algorithm ? `ALGORITHM: ${result.algorithm}` : 'DERIVING CIPHER PARAMETERS'
    },
    {
      id: 2,
      title: 'PINNING TO IPFS',
      detail: result?.ipfs_hash ? `IPFS: ${truncate(result.ipfs_hash)}` : 'AWAITING CONTENT ADDRESS'
    },
    {
      id: 3,
      title: 'WRITING TO BLOCKCHAIN',
      detail: result?.transaction_hash ? `TX: ${truncate(result.transaction_hash)}` : 'PREPARING IMMUTABLE LOG'
    }
  ];

  return (
    <section className="panel p-5 sm:p-6">
      <p className="terminal-label text-xs">LIVE OPERATION</p>
      <div className="mt-6 space-y-0">
        {stages.map((item, index) => {
          const active = stage === item.id && !error;
          const done = stage > item.id && !error;
          const failed = Boolean(error && stage === item.id);
          const dotStatus = failed ? 'error' : done ? 'done' : active ? 'active' : 'idle';

          return (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, x: -16 }}
              animate={stage >= item.id || item.id === 1 ? { opacity: 1, x: 0 } : { opacity: 0.35, x: 0 }}
              transition={{ duration: 0.3, delay: index * 0.08 }}
              className="grid grid-cols-[34px_1fr_auto] gap-4"
            >
              <div className="flex flex-col items-center">
                <div className="flex h-8 w-8 items-center justify-center border border-vault-border bg-black/40">
                  <StatusDot status={dotStatus} />
                </div>
                {index < stages.length - 1 && (
                  <div className="relative h-20 w-px bg-vault-border">
                    <motion.div
                      className="absolute left-0 top-0 w-px bg-cyan"
                      initial={{ height: '0%' }}
                      animate={{ height: done ? '100%' : '0%' }}
                      transition={{ duration: 0.35 }}
                    />
                  </div>
                )}
              </div>
              <div className="pb-8">
                <h3 className="font-display text-lg text-text-primary">{item.title}</h3>
                <p className={`mt-2 font-display text-xs ${failed ? 'text-danger' : 'text-text-muted'}`}>
                  {failed ? error : item.detail}
                </p>
              </div>
              <div className="font-display text-xs text-cyan">{stage >= item.id ? `${elapsed.toFixed(1)}s` : '--'}</div>
            </motion.div>
          );
        })}
      </div>
    </section>
  );
}
