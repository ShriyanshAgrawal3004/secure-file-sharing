import { motion } from 'framer-motion';
import { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import AlgorithmBadge from '../components/AlgorithmBadge.jsx';
import HashCard from '../components/HashCard.jsx';
import SecurityScore from '../components/SecurityScore.jsx';
import { mockFiles } from '../data/mockFiles.js';

function HighlightedJson({ data }) {
  const highlighted = JSON.stringify(data, null, 2)
    .replace(/("[^"]+":)/g, '<span class="syntax-key">$1</span>')
    .replace(/: ("[^"]*")/g, ': <span class="syntax-string">$1</span>')
    .replace(/[{}[\],]/g, '<span class="syntax-mark">$&</span>');

  return (
    <pre
      className="overflow-x-auto border border-vault-border bg-black/40 p-4 font-display text-xs leading-6 text-text-primary"
      dangerouslySetInnerHTML={{ __html: highlighted }}
    />
  );
}

export default function FileDetail() {
  const { id } = useParams();
  const [open, setOpen] = useState(false);
  const file = useMemo(() => mockFiles.find((entry) => entry.id === id), [id]);

  if (!file) {
    return (
      <section className="panel p-8">
        <p className="terminal-label text-xs">LOOKUP FAILURE</p>
        <h1 className="font-display mt-3 text-4xl text-danger">FILE NOT FOUND</h1>
        <Link to="/vault" className="cyan-button mt-6 inline-flex px-4 py-3 text-xs">RETURN TO VAULT</Link>
      </section>
    );
  }

  const raw = {
    id: file.id,
    filename: file.name,
    ipfsHash: file.ipfsHash,
    transactionHash: file.txHash,
    algorithm: file.algorithm,
    sensitivity: file.sensitivity,
    accessStatus: file.accessStatus,
    verifiedAt: '2025-05-24T14:32:00.000Z'
  };

  return (
    <section>
      <Link to="/vault" className="cyan-button mb-5 inline-flex px-4 py-3 text-xs">← BACK TO VAULT</Link>
      <div className="mb-7">
        <p className="terminal-label text-xs">FILE DETAIL / {file.id}</p>
        <h1 className="font-display mt-3 break-words text-4xl text-text-primary sm:text-6xl">{file.name}</h1>
      </div>

      <div className="grid gap-5 lg:grid-cols-[0.95fr_1.05fr]">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="panel p-6">
          <p className="terminal-label text-xs">METADATA</p>
          <div className="mt-6 grid gap-5">
            {[
              ['Name', file.name],
              ['Size', file.size],
              ['Timestamp', file.timestamp],
              ['Sensitivity', file.sensitivity],
              ['Access Status', file.accessStatus]
            ].map(([label, value]) => (
              <div key={label} className="grid grid-cols-[130px_1fr] gap-4 border-b border-vault-border pb-4 last:border-b-0">
                <span className="font-display text-xs uppercase text-text-muted">{label}</span>
                <span className={label === 'Sensitivity' ? 'font-display text-amber' : 'text-text-primary'}>{value}</span>
              </div>
            ))}
            <div className="pt-1">
              <AlgorithmBadge algorithm={file.algorithm} />
            </div>
          </div>
        </motion.div>

        <div className="grid gap-5">
          <SecurityScore sensitivity={file.sensitivity} />
          <div className="grid gap-4 sm:grid-cols-2">
            <HashCard label="IPFS HASH" value={file.ipfsHash} />
            <HashCard label="TX HASH" value={file.txHash} />
          </div>
        </div>
      </div>

      <section className="panel mt-5 p-5 sm:p-6">
        <button
          type="button"
          onClick={() => setOpen((value) => !value)}
          className="flex w-full items-center justify-between font-display text-sm text-cyan"
        >
          RAW CHAIN DATA <span>{open ? '▴' : '▾'}</span>
        </button>
        {open && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="mt-5">
            <HighlightedJson data={raw} />
          </motion.div>
        )}
      </section>
    </section>
  );
}
