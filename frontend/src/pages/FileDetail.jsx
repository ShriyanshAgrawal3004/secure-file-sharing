import { motion } from 'framer-motion';
import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import api from '../api.js';
import AlgorithmBadge from '../components/AlgorithmBadge.jsx';
import HashCard from '../components/HashCard.jsx';
import SecurityScore from '../components/SecurityScore.jsx';
import useAuth from '../hooks/useAuth.js';
import { fileToViewModel, truncateAddress } from '../utils/format.js';

function RequestRow({ item, actioning, onGrant, onDeny }) {
  return (
    <div className="grid gap-3 border border-vault-border bg-black/20 p-3 sm:grid-cols-[1fr_auto] sm:items-center">
      <div>
        <p className="font-display text-sm text-text-primary">{truncateAddress(item.requester_address)}</p>
        <p className="mt-1 font-display text-[11px] text-text-muted">{new Date(item.requested_at).toLocaleString()}</p>
      </div>
      <div className="flex gap-2">
        <button type="button" onClick={() => onGrant(item.requester_address)} disabled={actioning} className="cyan-button px-3 py-2 text-[11px]">
          GRANT ✓
        </button>
        <button type="button" onClick={() => onDeny(item.requester_address)} disabled={actioning} className="amber-button px-3 py-2 text-[11px]">
          DENY ✗
        </button>
      </div>
    </div>
  );
}

export default function FileDetail() {
  const { id } = useParams();
  const { walletAddress } = useAuth();
  const [file, setFile] = useState(null);
  const [pending, setPending] = useState([]);
  const [granted, setGranted] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actioning, setActioning] = useState(false);
  const [confirmRevoke, setConfirmRevoke] = useState('');

  const view = useMemo(() => (file ? fileToViewModel(file) : null), [file]);
  const isOwner = file?.owner_wallet?.toLowerCase() === walletAddress.toLowerCase();

  function load() {
    setLoading(true);
    setError('');
    return Promise.all([
      api.get(`/file/${id}`),
      api.get(`/file/${id}/access-list?status=PENDING`),
      api.get(`/file/${id}/access-list?status=GRANTED`)
    ])
      .then(([fileResponse, pendingResponse, grantedResponse]) => {
        setFile(fileResponse.data);
        setPending(pendingResponse.data.requests || []);
        setGranted(grantedResponse.data.requests || []);
      })
      .catch((requestError) => setError(requestError.response?.data?.error || requestError.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, [id]);

  async function grant(requester) {
    setActioning(true);
    setError('');
    try {
      await api.post('/grant_access', { file_id: Number(id), owner_address: walletAddress, user_address: requester });
      await load();
    } catch (requestError) {
      setError(requestError.response?.data?.error || requestError.message);
    } finally {
      setActioning(false);
    }
  }

  async function revoke(requester) {
    setActioning(true);
    setError('');
    try {
      await api.post('/revoke_access', { file_id: Number(id), owner_address: walletAddress, user_address: requester });
      setConfirmRevoke('');
      await load();
    } catch (requestError) {
      setError(requestError.response?.data?.error || requestError.message);
    } finally {
      setActioning(false);
    }
  }

  if (loading) {
    return <section className="panel p-8 font-display text-lg text-cyan">LOADING FILE DETAIL<span className="animate-blink">_</span></section>;
  }

  if (error && !file) {
    return (
      <section className="panel p-8">
        <p className="terminal-label text-xs">LOOKUP FAILURE</p>
        <h1 className="font-display mt-3 text-4xl text-danger">{error}</h1>
        <Link to="/vault" className="cyan-button mt-6 inline-flex px-4 py-3 text-xs">RETURN TO VAULT</Link>
      </section>
    );
  }

  if (!isOwner) {
    return (
      <section className="panel p-8">
        <p className="terminal-label text-xs">ACCESS CONTROL</p>
        <h1 className="font-display mt-3 text-4xl text-danger">403 OWNER ONLY</h1>
        <p className="mt-4 text-sm text-text-muted">This management view is restricted to the file owner.</p>
      </section>
    );
  }

  return (
    <section>
      <Link to="/vault" className="cyan-button mb-5 inline-flex px-4 py-3 text-xs">← BACK TO VAULT</Link>
      <div className="mb-7">
        <p className="terminal-label text-xs">FILE DETAIL / {view.id}</p>
        <h1 className="font-display mt-3 break-words text-4xl text-text-primary sm:text-6xl">{view.name}</h1>
      </div>
      {error && <p className="mb-5 border border-danger/50 bg-danger/10 p-3 font-display text-xs text-danger">{error}</p>}

      <div className="grid gap-5 lg:grid-cols-[0.95fr_1.05fr]">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="panel p-6">
          <p className="terminal-label text-xs">METADATA</p>
          <div className="mt-6 grid gap-5">
            {[
              ['Name', view.name],
              ['Size', view.size],
              ['Timestamp', view.timestamp],
              ['Sensitivity', view.sensitivity],
              ['Owner', truncateAddress(view.ownerWallet)]
            ].map(([label, value]) => (
              <div key={label} className="grid grid-cols-[130px_1fr] gap-4 border-b border-vault-border pb-4 last:border-b-0">
                <span className="font-display text-xs uppercase text-text-muted">{label}</span>
                <span className={label === 'Sensitivity' ? 'font-display text-amber' : 'break-words text-text-primary'}>{value}</span>
              </div>
            ))}
            <div className="pt-1">
              <AlgorithmBadge algorithm={view.algorithm} />
            </div>
          </div>
        </motion.div>

        <div className="grid gap-5">
          <SecurityScore sensitivity={view.sensitivity} />
          <div className="grid gap-4 sm:grid-cols-2">
            <HashCard label="IPFS HASH" value={view.ipfsHash} />
            <HashCard label="TX HASH" value={view.txHash} />
          </div>
        </div>
      </div>

      <section className="panel mt-5 p-5 sm:p-6">
        <h2 className="font-display text-xl text-amber">PENDING ACCESS REQUESTS</h2>
        <div className="mt-5 grid gap-3">
          {pending.length ? (
            pending.map((item) => (
              <RequestRow key={item.id} item={item} actioning={actioning} onGrant={grant} onDeny={revoke} />
            ))
          ) : (
            <p className="font-display text-sm text-cyan">NO PENDING REQUESTS<span className="animate-blink">_</span></p>
          )}
        </div>
      </section>

      <section className="panel mt-5 p-5 sm:p-6">
        <h2 className="font-display text-xl text-cyan">GRANTED ACCESS LIST</h2>
        <div className="mt-5 grid gap-3">
          {granted.length ? (
            granted.map((item) => (
              <div key={item.id} className="grid gap-3 border border-vault-border bg-black/20 p-3 sm:grid-cols-[1fr_auto] sm:items-center">
                <p className="font-display text-sm text-text-primary">{truncateAddress(item.requester_address)}</p>
                {confirmRevoke === item.requester_address ? (
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-display text-[11px] text-danger">REVOKE ACCESS FROM {truncateAddress(item.requester_address)}?</span>
                    <button type="button" onClick={() => revoke(item.requester_address)} disabled={actioning} className="amber-button px-3 py-2 text-[11px]">CONFIRM</button>
                    <button type="button" onClick={() => setConfirmRevoke('')} className="cyan-button px-3 py-2 text-[11px]">CANCEL</button>
                  </div>
                ) : (
                  <button type="button" onClick={() => setConfirmRevoke(item.requester_address)} className="amber-button px-3 py-2 text-[11px]">REVOKE</button>
                )}
              </div>
            ))
          ) : (
            <p className="font-display text-sm text-cyan">NO GRANTED USERS<span className="animate-blink">_</span></p>
          )}
        </div>
      </section>
    </section>
  );
}
