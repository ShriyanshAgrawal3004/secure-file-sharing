import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import AlgorithmBadge from '../components/AlgorithmBadge.jsx';
import api from '../api.js';
import useAuth from '../hooks/useAuth.js';
import { formatDate, truncateAddress } from '../utils/format.js';

export default function DashboardPage() {
  const { walletAddress } = useAuth();
  const [files, setFiles] = useState([]);
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError('');
    Promise.all([
      api.get(`/user/${walletAddress}/files`),
      api.get(`/user/${walletAddress}/pending-requests`)
    ])
      .then(([filesResponse, requestsResponse]) => {
        if (!mounted) return;
        setFiles(filesResponse.data.files || []);
        setRequests(requestsResponse.data.requests || []);
      })
      .catch((requestError) => mounted && setError(requestError.response?.data?.error || requestError.message))
      .finally(() => mounted && setLoading(false));
    return () => {
      mounted = false;
    };
  }, [walletAddress]);

  return (
    <section>
      <div className="mb-7">
        <p className="terminal-label text-xs">CONTROL SURFACE</p>
        <h1 className="font-display mt-3 text-5xl text-text-primary sm:text-7xl">DASHBOARD</h1>
      </div>
      {error && <p className="mb-5 border border-danger/50 bg-danger/10 p-3 font-display text-xs text-danger">{error}</p>}
      <div className="grid gap-5 xl:grid-cols-2">
        <section className="panel p-5 sm:p-6">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="font-display text-xl text-cyan">MY FILES</h2>
            <span className="border border-vault-border px-3 py-1 font-display text-lg text-text-primary">{files.length}</span>
          </div>
          {loading ? (
            <p className="font-display text-sm text-cyan">LOADING FILE INDEX<span className="animate-blink">_</span></p>
          ) : files.length ? (
            <div className="grid gap-3">
              {files.slice(0, 5).map((file) => (
                <Link key={file.file_id} to={`/file/${file.file_id}`} className="grid gap-2 border border-vault-border bg-black/20 p-3 transition hover:border-cyan sm:grid-cols-[1fr_auto_auto] sm:items-center">
                  <span className="truncate text-sm text-text-primary">{file.original_filename}</span>
                  <AlgorithmBadge algorithm={file.algorithm} />
                  <span className="font-display text-[11px] text-text-muted">{formatDate(file.created_at)}</span>
                </Link>
              ))}
            </div>
          ) : (
            <p className="font-display text-sm text-cyan">NO FILES ENCRYPTED YET<span className="animate-blink">_</span></p>
          )}
          <Link to="/vault" className="cyan-button mt-5 inline-flex px-4 py-3 text-xs">VIEW ALL →</Link>
        </section>

        <section className="panel p-5 sm:p-6">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="font-display text-xl text-amber">PENDING REQUESTS</h2>
            <span className="border border-vault-border px-3 py-1 font-display text-lg text-text-primary">{requests.length}</span>
          </div>
          {loading ? (
            <p className="font-display text-sm text-cyan">LOADING REQUEST QUEUE<span className="animate-blink">_</span></p>
          ) : requests.length ? (
            <div className="grid gap-3">
              {requests.map((item) => (
                <div key={item.id} className="grid gap-3 border border-vault-border bg-black/20 p-3 sm:grid-cols-[1fr_auto] sm:items-center">
                  <div>
                    <p className="truncate text-sm text-text-primary">{item.filename}</p>
                    <p className="mt-1 font-display text-[11px] text-text-muted">
                      {truncateAddress(item.requester_address)} / {formatDate(item.requested_at)}
                    </p>
                  </div>
                  <Link to={`/file/${item.file_id}`} className="amber-button px-3 py-2 text-center text-[11px]">REVIEW →</Link>
                </div>
              ))}
            </div>
          ) : (
            <p className="font-display text-sm text-cyan">NO PENDING REQUESTS<span className="animate-blink">_</span></p>
          )}
        </section>
      </div>
    </section>
  );
}
