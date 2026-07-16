import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api.js';
import useAuth from '../hooks/useAuth.js';

export default function ProfilePage() {
  const { walletAddress, displayName, logout, setUser } = useAuth();
  const [name, setName] = useState(displayName || '');
  const [files, setFiles] = useState([]);
  const [shared, setShared] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    Promise.all([
      api.get(`/user/${walletAddress}/files`),
      api.get(`/user/${walletAddress}/my-requests`)
    ])
      .then(([filesResponse, requestsResponse]) => {
        if (!mounted) return;
        setFiles(filesResponse.data.files || []);
        setShared((requestsResponse.data.requests || []).filter((item) => item.status === 'GRANTED'));
      })
      .catch((requestError) => mounted && setError(requestError.response?.data?.error || requestError.message))
      .finally(() => mounted && setLoading(false));
    return () => {
      mounted = false;
    };
  }, [walletAddress]);

  async function saveProfile() {
    setSaving(true);
    setError('');
    try {
      const response = await api.put(`/user/${walletAddress}/profile`, { display_name: name });
      setUser(response.data);
    } catch (requestError) {
      setError(requestError.response?.data?.error || requestError.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleLogout() {
    await logout();
    navigate('/login', { replace: true });
  }

  return (
    <section>
      <div className="mb-7">
        <p className="terminal-label text-xs">IDENTITY NODE</p>
        <h1 className="font-display mt-3 text-5xl text-text-primary sm:text-7xl">PROFILE</h1>
      </div>
      {error && <p className="mb-5 border border-danger/50 bg-danger/10 p-3 font-display text-xs text-danger">{error}</p>}
      <div className="grid gap-5 lg:grid-cols-[1fr_0.7fr]">
        <section className="panel p-5 sm:p-6">
          <label className="block">
            <span className="terminal-label text-[11px]">WALLET ADDRESS</span>
            <input readOnly value={walletAddress} className="mt-2 w-full border border-vault-border bg-black/30 px-4 py-3 font-display text-xs text-text-primary outline-none" />
          </label>
          <label className="mt-5 block">
            <span className="terminal-label text-[11px]">DISPLAY NAME</span>
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Optional callsign"
              className="mt-2 w-full border border-vault-border bg-black/30 px-4 py-3 font-display text-sm text-text-primary outline-none transition placeholder:text-text-muted focus:border-cyan focus:shadow-cyan"
            />
          </label>
          <div className="mt-5 flex flex-wrap gap-3">
            <button type="button" onClick={saveProfile} disabled={saving} className="cyan-button px-4 py-3 text-xs">
              {saving ? 'SAVING' : 'SAVE PROFILE'}
            </button>
            <button type="button" onClick={handleLogout} className="amber-button px-4 py-3 text-xs">LOGOUT</button>
          </div>
        </section>
        <section className="panel grid gap-4 p-5 sm:p-6">
          {loading ? (
            <p className="font-display text-lg text-cyan">LOADING COUNTS<span className="animate-blink">_</span></p>
          ) : (
            <>
              <div className="border border-vault-border bg-black/20 p-4">
                <p className="terminal-label text-[11px]">TOTAL FILES UPLOADED</p>
                <p className="font-display mt-2 text-4xl text-cyan">{files.length}</p>
              </div>
              <div className="border border-vault-border bg-black/20 p-4">
                <p className="terminal-label text-[11px]">TOTAL FILES SHARED WITH ME</p>
                <p className="font-display mt-2 text-4xl text-amber">{shared.length}</p>
              </div>
            </>
          )}
        </section>
      </div>
    </section>
  );
}
