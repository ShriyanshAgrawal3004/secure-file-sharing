import axios from 'axios';
import { motion } from 'framer-motion';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import EncryptionStepper from '../components/EncryptionStepper.jsx';
import FileDropzone from '../components/FileDropzone.jsx';
import HashCard from '../components/HashCard.jsx';
import SensitivitySelector, { sensitivityLevels } from '../components/SensitivitySelector.jsx';

const API_URL = 'http://127.0.0.1:5000/upload';

const container = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.1 }
  }
};

const item = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35 } }
};

function fileIdFromResult(result) {
  return result?.ipfs_hash ? `CV-${result.ipfs_hash.slice(-8).toUpperCase()}` : 'CV-PENDING';
}

export default function Upload() {
  const [fileMeta, setFileMeta] = useState(null);
  const [sensitivity, setSensitivity] = useState('HIGH');
  const [ownerAddress, setOwnerAddress] = useState('');
  const [error, setError] = useState('');
  const [stage, setStage] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [result, setResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const timers = useRef([]);
  const activeLevel = useMemo(() => sensitivityLevels.find((level) => level.key === sensitivity), [sensitivity]);

  useEffect(() => () => timers.current.forEach(window.clearTimeout), []);

  useEffect(() => {
    if (!submitting) return undefined;
    const started = performance.now();
    const interval = window.setInterval(() => {
      setElapsed((performance.now() - started) / 1000);
    }, 100);
    return () => window.clearInterval(interval);
  }, [submitting]);

  function reset() {
    timers.current.forEach(window.clearTimeout);
    timers.current = [];
    setFileMeta(null);
    setOwnerAddress('');
    setError('');
    setStage(0);
    setElapsed(0);
    setResult(null);
    setSubmitting(false);
  }

  async function submit() {
    if (!fileMeta?.file) {
      setError('UPLOAD BLOCKED: SELECT A FILE BEFORE ENCRYPTION');
      return;
    }

    if (!ownerAddress.trim()) {
      setError('UPLOAD BLOCKED: ENTER THE OWNER WALLET ADDRESS');
      return;
    }

    timers.current.forEach(window.clearTimeout);
    timers.current = [
      window.setTimeout(() => setStage(2), 1200),
      window.setTimeout(() => setStage(3), 2400)
    ];

    setError('');
    setResult(null);
    setElapsed(0);
    setStage(1);
    setSubmitting(true);

    const formData = new FormData();
    formData.append('file', fileMeta.file);
    formData.append('sensitivity', activeLevel.apiValue);
    formData.append('owner_address', ownerAddress.trim());

    try {
      const response = await axios.post(API_URL, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      timers.current.forEach(window.clearTimeout);
      timers.current = [];
      setStage(4);
      setResult(response.data);
    } catch (requestError) {
      timers.current.forEach(window.clearTimeout);
      timers.current = [];
      const message = requestError.response?.data?.error || requestError.response?.data?.message || requestError.message;
      setError(`API ERROR: ${message}`);
    } finally {
      setSubmitting(false);
    }
  }

  if (result) {
    return (
      <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mx-auto max-w-5xl">
        <div className="panel p-6 text-center sm:p-10">
          <svg viewBox="0 0 120 120" className="mx-auto h-28 w-28">
            <circle cx="60" cy="60" r="50" fill="none" stroke="rgba(0,229,255,0.13)" strokeWidth="2" />
            <motion.path
              d="M34 62 L52 80 L88 40"
              fill="none"
              stroke="#00E5FF"
              strokeWidth="8"
              strokeLinecap="square"
              strokeLinejoin="miter"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 0.6, ease: 'easeInOut' }}
            />
          </svg>
          <h1 className="font-display mt-5 text-5xl text-cyan drop-shadow-[0_0_24px_rgba(0,229,255,0.38)]">SECURED</h1>
          <p className="mx-auto mt-3 max-w-2xl text-sm leading-6 text-text-muted">{result.message || 'Payload encrypted, pinned, and written to chain.'}</p>
        </div>

        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <HashCard label="ALGORITHM" value={result.algorithm || 'UNKNOWN'} copyable={false} />
          <HashCard label="IPFS HASH" value={result.ipfs_hash} />
          <HashCard label="TX HASH" value={result.transaction_hash} />
          <HashCard label="FILE ID" value={fileIdFromResult(result)} />
        </div>

        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          <Link to="/vault" className="cyan-button px-5 py-4 text-center text-sm">VIEW IN VAULT →</Link>
          <button type="button" onClick={reset} className="amber-button px-5 py-4 text-sm">ENCRYPT ANOTHER</button>
        </div>
      </motion.section>
    );
  }

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="mx-auto max-w-6xl">
      <motion.section variants={item} className="mb-8">
        <p className="terminal-label text-xs">CLASSIFIED FILE SYSTEM</p>
        <h1 className="font-display mt-3 text-5xl leading-tight text-text-primary sm:text-7xl">
          ENCRYPTED <span className="text-cyan">COLD</span> STORAGE
        </h1>
        <p className="mt-4 max-w-3xl text-base leading-7 text-text-muted">
          Local checksum verification, sensitivity-driven encryption routing, IPFS pinning, and immutable chain logging in one locked upload path.
        </p>
      </motion.section>

      <div className="grid gap-5 lg:grid-cols-[1.25fr_0.75fr]">
        <motion.div variants={item}>
          <FileDropzone fileMeta={fileMeta} onFileReady={setFileMeta} onError={setError} />
        </motion.div>
        <motion.div variants={item} className="space-y-5">
          <SensitivitySelector value={sensitivity} onChange={setSensitivity} />
          <section className="panel p-5 sm:p-6">
            <p className="terminal-label text-xs">STEP 03 / COMMIT</p>
            <label className="mt-4 block">
              <span className="terminal-label text-[11px]">OWNER WALLET ADDRESS</span>
              <input
                value={ownerAddress}
                onChange={(event) => setOwnerAddress(event.target.value)}
                placeholder="0x..."
                className="mt-2 w-full border border-vault-border bg-black/30 px-4 py-3 font-display text-xs text-text-primary outline-none transition placeholder:text-text-muted focus:border-cyan focus:shadow-cyan"
              />
            </label>
            <button
              type="button"
              onClick={submit}
              disabled={submitting}
              className="amber-button mt-5 w-full px-5 py-5 text-base disabled:cursor-wait disabled:opacity-60"
            >
              {submitting ? 'OPERATION RUNNING' : 'ENCRYPT & STORE →'}
            </button>
            {error && <p className="mt-4 border border-danger/50 bg-danger/10 p-3 font-display text-xs text-danger">{error}</p>}
          </section>
        </motion.div>
      </div>

      {(stage > 0 || submitting || error.startsWith('API ERROR')) && (
        <motion.div variants={item} className="mt-5">
          <EncryptionStepper stage={stage || 1} elapsed={elapsed} result={result} error={error.startsWith('API ERROR') ? error : ''} />
        </motion.div>
      )}
    </motion.div>
  );
}
