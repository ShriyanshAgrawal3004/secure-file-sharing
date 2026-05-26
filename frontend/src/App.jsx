import { AnimatePresence, motion } from 'framer-motion';
import { Link, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import ChainStatusBar from './components/ChainStatusBar.jsx';
import Upload from './pages/Upload.jsx';
import Vault from './pages/Vault.jsx';
import FileDetail from './pages/FileDetail.jsx';

const pageVariants = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 8 }
};

function Layout() {
  const location = useLocation();

  return (
    <div className="vault-shell">
      <div className="scan-sweep" />
      <ChainStatusBar />
      <header className="relative z-20 mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-5 sm:px-6 lg:px-8">
        <Link to="/upload" className="font-display text-xl text-cyan drop-shadow-[0_0_18px_rgba(0,229,255,0.32)]">
          COLD VAULT
        </Link>
        <nav className="flex items-center gap-2 font-display text-xs uppercase text-text-muted">
          <Link className="border border-vault-border px-3 py-2 transition hover:border-cyan hover:text-cyan" to="/upload">
            Upload
          </Link>
          <Link className="border border-vault-border px-3 py-2 transition hover:border-cyan hover:text-cyan" to="/vault">
            Vault
          </Link>
        </nav>
      </header>
      <main className="relative z-20 mx-auto w-full max-w-7xl px-4 pb-14 sm:px-6 lg:px-8">
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
              <Route path="/" element={<Navigate to="/upload" replace />} />
              <Route path="/upload" element={<Upload />} />
              <Route path="/vault" element={<Vault />} />
              <Route path="/file/:id" element={<FileDetail />} />
              <Route path="*" element={<Navigate to="/upload" replace />} />
            </Routes>
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}

export default function App() {
  return <Layout />;
}
