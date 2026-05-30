import { motion } from 'framer-motion';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuth from '../hooks/useAuth.js';

const walletPattern = /^0x[a-fA-F0-9]{40}$/;

export default function LoginPage() {
  const [wallet, setWallet] = useState(localStorage.getItem('coldVaultWallet') || '');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function submit(event) {
    event.preventDefault();
    if (!walletPattern.test(wallet.trim())) {
      setError('INVALID WALLET FORMAT: EXPECTED 0x + 40 HEX CHARACTERS');
      return;
    }

    setSubmitting(true);
    setError('');
    try {
      await login(wallet.trim());
      navigate('/dashboard', { replace: true });
    } catch (requestError) {
      setError(requestError.response?.data?.error || requestError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="relative z-20 flex min-h-screen items-center justify-center px-4 py-12">
      <motion.form
        onSubmit={submit}
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="panel w-full max-w-xl p-6 text-center sm:p-10"
      >
        <p className="terminal-label text-xs">SECURE SESSION</p>
        <h1 className="font-display mt-4 text-5xl text-cyan drop-shadow-[0_0_24px_rgba(0,229,255,0.38)] sm:text-7xl">
          COLD VAULT
        </h1>
        <p className="mt-4 text-sm text-text-muted">Enter your wallet address to continue</p>
        <input
          value={wallet}
          onChange={(event) => setWallet(event.target.value)}
          placeholder="0x..."
          className={`mt-8 w-full border bg-black/30 px-4 py-4 font-display text-xs text-text-primary outline-none transition placeholder:text-text-muted focus:border-cyan focus:shadow-cyan ${
            error ? 'border-danger shadow-danger' : 'border-vault-border'
          }`}
        />
        {error && <p className="mt-3 border border-danger/50 bg-danger/10 p-3 text-left font-display text-xs text-danger">{error}</p>}
        <button type="submit" disabled={submitting} className="cyan-button mt-5 w-full px-5 py-4 text-sm disabled:cursor-wait disabled:opacity-60">
          {submitting ? 'CONNECTING' : 'CONNECT ->'}
        </button>
      </motion.form>
    </main>
  );
}
