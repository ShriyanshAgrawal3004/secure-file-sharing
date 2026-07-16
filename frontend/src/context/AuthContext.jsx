import { createContext, useEffect, useMemo, useState } from 'react';
import api from '../api.js';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    api
      .get('/auth/me')
      .then((response) => {
        if (!mounted) return;
        setUser(response.data);
        localStorage.setItem('coldVaultWallet', response.data.wallet_address);
      })
      .catch(() => {
        if (!mounted) return;
        localStorage.removeItem('coldVaultWallet');
        setUser(null);
      })
      .finally(() => mounted && setLoading(false));

    return () => {
      mounted = false;
    };
  }, []);

  async function login(walletAddress) {
    const response = await api.post('/auth/login', { wallet_address: walletAddress });
    setUser(response.data);
    localStorage.setItem('coldVaultWallet', response.data.wallet_address);
    return response.data;
  }

  async function logout() {
    await api.post('/auth/logout');
    localStorage.removeItem('coldVaultWallet');
    setUser(null);
  }

  const value = useMemo(
    () => ({
      walletAddress: user?.wallet_address || '',
      displayName: user?.display_name || '',
      createdAt: user?.created_at || '',
      isLoggedIn: Boolean(user?.wallet_address),
      loading,
      login,
      logout,
      setUser
    }),
    [loading, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
