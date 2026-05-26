import { motion } from 'framer-motion';
import { useRef, useState } from 'react';

const MAX_BYTES = 25 * 1024 * 1024;

function formatBytes(bytes) {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

async function sha256(file) {
  const buffer = await file.arrayBuffer();
  const digest = await crypto.subtle.digest('SHA-256', buffer);
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, '0'))
    .join('');
}

export default function FileDropzone({ fileMeta, onFileReady, onError }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);

  async function acceptFile(file) {
    if (!file) return;
    if (file.size > MAX_BYTES) {
      onError('FILE REJECTED: MAXIMUM SIZE IS 25 MB');
      return;
    }

    setBusy(true);
    onError('');
    try {
      const checksum = await sha256(file);
      onFileReady({
        file,
        name: file.name,
        size: formatBytes(file.size),
        type: file.type || 'application/octet-stream',
        checksum
      });
    } catch {
      onError('CHECKSUM FAILURE: WEB CRYPTO DIGEST UNAVAILABLE');
    } finally {
      setBusy(false);
    }
  }

  function handleDrop(event) {
    event.preventDefault();
    setDragging(false);
    acceptFile(event.dataTransfer.files?.[0]);
  }

  return (
    <motion.div
      animate={{ scale: dragging ? 1.02 : 1 }}
      transition={{ type: 'spring', stiffness: 260, damping: 22 }}
      onDragOver={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={`panel relative min-h-[270px] cursor-pointer overflow-hidden border-dashed p-7 transition ${
        dragging ? 'border-cyan shadow-cyan' : 'hover:border-cyan/70'
      }`}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        onChange={(event) => acceptFile(event.target.files?.[0])}
      />
      <div className="absolute inset-x-0 top-0 h-px bg-cyan/50" />
      <div className="flex h-full min-h-[216px] flex-col justify-between gap-8">
        <div>
          <p className="terminal-label text-xs">STEP 01 / DROP ZONE</p>
          <h2 className="font-display mt-5 text-3xl text-text-primary sm:text-4xl">
            {fileMeta ? 'PAYLOAD LOCKED' : busy ? 'HASHING PAYLOAD' : 'DROP FILE FOR COLD STORAGE'}
          </h2>
          <p className="mt-4 max-w-2xl text-sm leading-6 text-text-muted">
            Drag a file into the perimeter or click to browse. The vault computes SHA-256 locally before encryption begins.
          </p>
        </div>

        {fileMeta ? (
          <div className="grid gap-3 border-t border-vault-border pt-5 sm:grid-cols-2">
            <div>
              <p className="terminal-label text-[11px]">FILENAME</p>
              <p className="mt-1 text-sm text-text-primary">{fileMeta.name}</p>
            </div>
            <div>
              <p className="terminal-label text-[11px]">SIZE / TYPE</p>
              <p className="mt-1 text-sm text-text-primary">{fileMeta.size} / {fileMeta.type}</p>
            </div>
            <div className="sm:col-span-2">
              <p className="terminal-label text-[11px]">SHA-256 CHECKSUM</p>
              <p className="hash-text mt-1 text-xs leading-5">{fileMeta.checksum}</p>
            </div>
          </div>
        ) : (
          <div className="border border-vault-border bg-black/20 p-4 font-display text-xs uppercase text-text-muted">
            ACCEPTING BINARY INPUT / MAX 25 MB / HASH REQUIRED
          </div>
        )}
      </div>
    </motion.div>
  );
}
