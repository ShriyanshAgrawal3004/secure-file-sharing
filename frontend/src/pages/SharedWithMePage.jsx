import { useEffect, useMemo, useState } from 'react';
import AlgorithmBadge from '../components/AlgorithmBadge.jsx';
import api from '../api.js';
import useAuth from '../hooks/useAuth.js';
import { formatBytes, truncateAddress } from '../utils/format.js';

export default function SharedWithMePage() {
  const { walletAddress } = useAuth();
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    api
      .get(`/user/${walletAddress}/my-requests`)
      .then((response) => mounted && setRequests(response.data.requests || []))
      .catch((requestError) => mounted && setError(requestError.response?.data?.error || requestError.message))
      .finally(() => mounted && setLoading(false));
    return () => {
      mounted = false;
    };
  }, [walletAddress]);

  const granted = useMemo(() => requests.filter((item) => item.status === 'GRANTED'), [requests]);

  return (
    <section>
      <div className="mb-7">
        <p className="terminal-label text-xs">AUTHORIZED DOWNLOADS</p>
        <h1 className="font-display mt-3 text-5xl text-text-primary sm:text-7xl">SHARED FILES</h1>
      </div>
      {error && <p className="mb-5 border border-danger/50 bg-danger/10 p-3 font-display text-xs text-danger">{error}</p>}
      {loading ? (
        <div className="panel p-8 font-display text-lg text-cyan">LOADING SHARED FILES<span className="animate-blink">_</span></div>
      ) : granted.length ? (
        <div className="grid gap-4 lg:grid-cols-2">
          {granted.map((item) => (
            <article key={item.id} className="panel p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="truncate text-lg font-bold text-text-primary">{item.filename}</h2>
                  <p className="mt-1 font-display text-xs text-text-muted">OWNER {truncateAddress(item.owner_wallet)}</p>
                </div>
                <AlgorithmBadge algorithm={item.algorithm} />
              </div>
              <div className="mt-5 grid grid-cols-2 gap-3 border-t border-vault-border pt-4 text-sm">
                <span className="text-text-muted">Size</span><span>{formatBytes(item.file_size)}</span>
                <span className="text-text-muted">File ID</span><span className="font-display text-cyan">{item.file_id}</span>
              </div>
              <a className="amber-button mt-5 inline-flex px-4 py-3 text-xs" href={`http://127.0.0.1:5000/decrypt/${encodeURIComponent(item.filename)}?wallet_address=${walletAddress}`}>
                DOWNLOAD
              </a>
            </article>
          ))}
        </div>
      ) : (
        <div className="panel p-8 font-display text-lg text-cyan">NO SHARED FILES<span className="animate-blink">_</span></div>
      )}
    </section>
  );
}
