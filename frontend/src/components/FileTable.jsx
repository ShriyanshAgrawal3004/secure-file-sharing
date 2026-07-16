import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import AlgorithmBadge from './AlgorithmBadge.jsx';

export default function FileTable({ files, walletAddress }) {
  if (!files.length) {
    return (
      <div className="panel p-8 font-display text-lg text-cyan">
        NO FILES ENCRYPTED YET<span className="animate-blink">_</span>
      </div>
    );
  }

  return (
    <>
      <div className="hidden overflow-hidden border border-vault-border md:block">
        <table className="w-full border-collapse bg-vault-panel/85 text-left">
          <thead className="font-display text-[11px] uppercase text-text-muted">
            <tr className="border-b border-vault-border">
              <th className="px-4 py-3 font-normal">File</th>
              <th className="px-4 py-3 font-normal">Size</th>
              <th className="px-4 py-3 font-normal">Timestamp</th>
              <th className="px-4 py-3 font-normal">Algorithm</th>
              <th className="px-4 py-3 font-normal">Sensitivity</th>
              <th className="px-4 py-3 font-normal">Access</th>
              <th className="px-4 py-3 font-normal" />
            </tr>
          </thead>
          <tbody>
            {files.map((file, index) => (
              <motion.tr
                key={file.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.08 }}
                className="group border-b border-vault-border/80 text-sm transition hover:bg-cyan/5"
              >
                <td className="px-4 py-4 font-medium text-text-primary">{file.name}</td>
                <td className="px-4 py-4 text-text-muted">{file.size}</td>
                <td className="px-4 py-4 font-display text-xs text-text-muted">{file.timestamp}</td>
                <td className="px-4 py-4"><AlgorithmBadge algorithm={file.algorithm} /></td>
                <td className="px-4 py-4 font-display text-xs text-amber">{file.sensitivity}</td>
                <td className="px-4 py-4 font-display text-xs text-cyan">{file.accessStatus}</td>
                <td className="px-4 py-4">
                  <div className="flex translate-x-4 justify-end gap-2 opacity-0 transition group-hover:translate-x-0 group-hover:opacity-100">
                    <Link className="cyan-button px-3 py-2 text-[11px]" to={`/file/${file.id}`}>VIEW</Link>
                    <a className="amber-button px-3 py-2 text-[11px]" href={`http://127.0.0.1:5000/decrypt/${encodeURIComponent(file.name)}?wallet_address=${walletAddress}`}>DOWNLOAD</a>
                  </div>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid gap-4 md:hidden">
        {files.map((file, index) => (
          <motion.article
            key={file.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.08 }}
            className="panel p-4"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-base font-bold text-text-primary">{file.name}</h3>
                <p className="mt-1 font-display text-xs text-text-muted">{file.timestamp}</p>
              </div>
              <AlgorithmBadge algorithm={file.algorithm} />
            </div>
            <div className="mt-5 grid grid-cols-2 gap-3 border-t border-vault-border pt-4 text-sm">
              <span className="text-text-muted">Size</span><span>{file.size}</span>
              <span className="text-text-muted">Sensitivity</span><span className="font-display text-amber">{file.sensitivity}</span>
              <span className="text-text-muted">Access</span><span className="font-display text-cyan">{file.accessStatus}</span>
            </div>
            <div className="mt-5 flex gap-2">
              <Link className="cyan-button flex-1 px-3 py-2 text-center text-xs" to={`/file/${file.id}`}>VIEW</Link>
              <a className="amber-button flex-1 px-3 py-2 text-center text-xs" href={`http://127.0.0.1:5000/decrypt/${encodeURIComponent(file.name)}?wallet_address=${walletAddress}`}>DOWNLOAD</a>
            </div>
          </motion.article>
        ))}
      </div>
    </>
  );
}
