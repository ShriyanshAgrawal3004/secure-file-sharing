import { useEffect, useState } from 'react';
import api from '../api.js';
import useAuth from '../hooks/useAuth.js';
import { formatDate, truncateAddress } from '../utils/format.js';

const statusClass = {
  PENDING: 'border-amber/60 bg-amber/10 text-amber',
  GRANTED: 'border-cyan/60 bg-cyan/10 text-cyan',
  DENIED: 'border-danger/60 bg-danger/10 text-danger'
};

export default function MyRequestsPage() {
  const { walletAddress } = useAuth();
  const [requests, setRequests] = useState([]);
  const [fileId, setFileId] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  function load() {
    setLoading(true);
    setError('');
    return api
      .get(`/user/${walletAddress}/my-requests`)
      .then((response) => setRequests(response.data.requests || []))
      .catch((requestError) => setError(requestError.response?.data?.error || requestError.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, [walletAddress]);

  async function requestAccess(event) {
    event.preventDefault();
    if (!fileId || Number(fileId) <= 0) {
      setError('ENTER A VALID FILE ID');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      const response = await api.post('/request_access', { file_id: Number(fileId), user_address: walletAddress });
      setRequests((current) => [response.data.request, ...current.filter((item) => item.id !== response.data.request.id)]);
      setFileId('');
    } catch (requestError) {
      setError(requestError.response?.data?.error || requestError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section>
      <div className="mb-7">
        <p className="terminal-label text-xs">REQUEST LEDGER</p>
        <h1 className="font-display mt-3 text-5xl text-text-primary sm:text-7xl">MY REQUESTS</h1>
      </div>
      <form onSubmit={requestAccess} className="panel mb-5 grid gap-4 p-4 sm:grid-cols-[1fr_auto] sm:items-end">
        <label>
          <span className="terminal-label text-[11px]">FILE ID NUMBER</span>
          <input
            value={fileId}
            onChange={(event) => setFileId(event.target.value)}
            type="number"
            min="1"
            placeholder="7"
            className="mt-2 w-full border border-vault-border bg-black/30 px-4 py-3 font-display text-sm text-text-primary outline-none transition placeholder:text-text-muted focus:border-cyan focus:shadow-cyan"
          />
        </label>
        <button type="submit" disabled={submitting} className="amber-button px-5 py-3 text-sm disabled:cursor-wait disabled:opacity-60">
          {submitting ? 'REQUESTING' : 'REQUEST ACCESS'}
        </button>
      </form>
      {error && <p className="mb-5 border border-danger/50 bg-danger/10 p-3 font-display text-xs text-danger">{error}</p>}
      {loading ? (
        <div className="panel p-8 font-display text-lg text-cyan">LOADING REQUESTS<span className="animate-blink">_</span></div>
      ) : requests.length ? (
        <div className="panel overflow-hidden">
          <div className="hidden md:block">
            <table className="w-full text-left">
              <thead className="border-b border-vault-border font-display text-[11px] uppercase text-text-muted">
                <tr>
                  <th className="px-4 py-3 font-normal">File</th>
                  <th className="px-4 py-3 font-normal">Owner</th>
                  <th className="px-4 py-3 font-normal">Status</th>
                  <th className="px-4 py-3 font-normal">Date</th>
                </tr>
              </thead>
              <tbody>
                {requests.map((item) => (
                  <tr key={item.id} className="border-b border-vault-border/80 text-sm">
                    <td className="px-4 py-4 text-text-primary">{item.filename}</td>
                    <td className="px-4 py-4 font-display text-xs text-text-muted">{truncateAddress(item.owner_wallet)}</td>
                    <td className="px-4 py-4">
                      <span className={`border px-2 py-1 font-display text-[11px] ${statusClass[item.status] || statusClass.PENDING}`}>{item.status}</span>
                    </td>
                    <td className="px-4 py-4 font-display text-xs text-text-muted">{formatDate(item.requested_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="grid gap-3 p-4 md:hidden">
            {requests.map((item) => (
              <article key={item.id} className="border border-vault-border bg-black/20 p-3">
                <div className="flex items-start justify-between gap-3">
                  <h2 className="text-sm font-bold text-text-primary">{item.filename}</h2>
                  <span className={`border px-2 py-1 font-display text-[11px] ${statusClass[item.status] || statusClass.PENDING}`}>{item.status}</span>
                </div>
                <p className="mt-2 font-display text-xs text-text-muted">OWNER {truncateAddress(item.owner_wallet)} / {formatDate(item.requested_at)}</p>
              </article>
            ))}
          </div>
        </div>
      ) : (
        <div className="panel p-8 font-display text-lg text-cyan">NO REQUEST HISTORY<span className="animate-blink">_</span></div>
      )}
    </section>
  );
}
