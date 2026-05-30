import { AnimatePresence, motion } from 'framer-motion';
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import ChainStatusBar from './components/ChainStatusBar.jsx';
import ProtectedRoute from './components/ProtectedRoute.jsx';
import { AuthProvider } from './context/AuthContext.jsx';
import useAuth from './hooks/useAuth.js';
import DashboardPage from './pages/DashboardPage.jsx';
import FileDetail from './pages/FileDetail.jsx';
import LoginPage from './pages/LoginPage.jsx';
import MyRequestsPage from './pages/MyRequestsPage.jsx';
import ProfilePage from './pages/ProfilePage.jsx';
import SharedWithMePage from './pages/SharedWithMePage.jsx';
import Upload from './pages/Upload.jsx';
import Vault from './pages/Vault.jsx';
import { truncateAddress } from './utils/format.js';

const pageVariants = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 8 }
};

const navItems = [
  ['Dashboard', '/dashboard', 'M4 13h6V4H4v9Zm10 7h6V4h-6v16ZM4 20h6v-5H4v5Zm10 0h6v-5h-6v5Z'],
  ['Upload', '/upload', 'M12 3 6 9h4v8h4V9h4l-6-6ZM5 19h14v2H5v-2Z'],
  ['My Vault', '/vault', 'M5 5h14v14H5V5Zm3 3v8h8V8H8Zm2 2h4v4h-4v-4Z'],
  ['Shared Files', '/shared-with-me', 'M8 12a4 4 0 1 1 7.5 2H18l3 3-3 3h-2.5A4 4 0 1 1 8 12Zm0 2a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z'],
  ['My Requests', '/my-requests', 'M4 5h16v3H4V5Zm0 6h16v3H4v-3Zm0 6h10v3H4v-3Z'],
  ['Profile', '/profile', 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm-7 9a7 7 0 0 1 14 0H5Z']
];

function Icon({ path }) {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4 fill-current" aria-hidden="true">
      <path d={path} />
    </svg>
  );
}

function Sidebar() {
  const location = useLocation();
  const { walletAddress } = useAuth();

  return (
    <aside className="panel flex flex-col p-4 lg:min-h-[calc(100vh-92px)]">
      <Link to="/dashboard" className="font-display text-xl text-cyan drop-shadow-[0_0_18px_rgba(0,229,255,0.32)]">
        COLD VAULT
      </Link>
      <nav className="mt-8 grid gap-2 font-display text-xs uppercase text-text-muted">
        {navItems.map(([label, to, icon]) => {
          const active = location.pathname === to;
          return (
            <Link
              key={to}
              to={to}
              className={`flex items-center gap-3 border px-3 py-3 transition ${
                active ? 'border-cyan bg-cyan/10 text-cyan shadow-cyan' : 'border-vault-border bg-black/10 hover:border-cyan hover:text-cyan'
              }`}
            >
              <Icon path={icon} />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="mt-8 border-t border-vault-border pt-4 lg:mt-auto">
        <p className="terminal-label text-[10px]">ACTIVE WALLET</p>
        <div className="mt-2 flex items-center gap-2 font-display text-xs text-text-primary">
          <span className="h-2 w-2 bg-success shadow-[0_0_14px_rgba(0,230,118,0.9)]" />
          {truncateAddress(walletAddress)}
        </div>
      </div>
    </aside>
  );
}

function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { walletAddress, logout } = useAuth();
  const isLogin = location.pathname === '/login';

  async function handleLogout() {
    await logout();
    navigate('/login', { replace: true });
  }

  if (isLogin) {
    return (
      <div className="vault-shell">
        <div className="scan-sweep" />
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </div>
    );
  }

  return (
    <div className="vault-shell">
      <div className="scan-sweep" />
      <ChainStatusBar walletAddress={walletAddress} onLogout={handleLogout} />
      <div className="relative z-20 mx-auto grid w-full max-w-7xl gap-5 px-4 py-5 sm:px-6 lg:grid-cols-[240px_1fr] lg:px-8">
        <Sidebar />
        <main className="min-w-0">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={{ duration: 0.25, ease: 'easeOut' }}
            >
              <Routes location={location}>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
                <Route path="/upload" element={<ProtectedRoute><Upload /></ProtectedRoute>} />
                <Route path="/vault" element={<ProtectedRoute><Vault /></ProtectedRoute>} />
                <Route path="/file/:id" element={<ProtectedRoute><FileDetail /></ProtectedRoute>} />
                <Route path="/shared-with-me" element={<ProtectedRoute><SharedWithMePage /></ProtectedRoute>} />
                <Route path="/my-requests" element={<ProtectedRoute><MyRequestsPage /></ProtectedRoute>} />
                <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Layout />
    </AuthProvider>
  );
}
