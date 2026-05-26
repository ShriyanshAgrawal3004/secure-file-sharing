import { useMemo, useState } from 'react';
import FileTable from '../components/FileTable.jsx';
import { mockFiles } from '../data/mockFiles.js';

export default function Vault() {
  const [query, setQuery] = useState('');
  const [algorithm, setAlgorithm] = useState('ALL');

  const filtered = useMemo(() => {
    return mockFiles.filter((file) => {
      const nameMatch = file.name.toLowerCase().includes(query.toLowerCase());
      const algorithmMatch = algorithm === 'ALL' || file.algorithm === algorithm;
      return nameMatch && algorithmMatch;
    });
  }, [algorithm, query]);

  return (
    <section>
      <div className="mb-7 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="terminal-label text-xs">ARCHIVE INDEX</p>
          <h1 className="font-display mt-3 text-5xl text-text-primary sm:text-7xl">FILE VAULT</h1>
        </div>
        <div className="inline-flex w-fit items-center gap-3 border border-vault-border bg-vault-panel px-4 py-3 font-display text-xs text-cyan">
          LIVE COUNT <span className="text-2xl text-text-primary">{filtered.length}</span>
        </div>
      </div>

      <div className="panel mb-5 grid gap-4 p-4 lg:grid-cols-[1fr_auto]">
        <label className="block">
          <span className="terminal-label text-[11px]">SEARCH BY FILENAME</span>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="contract_v2.pdf"
            className="mt-2 w-full border border-vault-border bg-black/30 px-4 py-3 font-display text-sm text-text-primary outline-none transition placeholder:text-text-muted focus:border-cyan focus:shadow-cyan"
          />
        </label>

        <div>
          <span className="terminal-label text-[11px]">ALGORITHM</span>
          <div className="mt-2 flex border border-vault-border">
            {['ALL', 'AES', 'CHACHA'].map((option, index) => (
              <button
                key={option}
                type="button"
                onClick={() => setAlgorithm(option)}
                className={`px-4 py-3 font-display text-xs transition ${
                  index > 0 ? 'border-l border-vault-border' : ''
                } ${
                  algorithm === option ? 'bg-cyan/10 text-cyan shadow-cyan' : 'bg-black/20 text-text-muted hover:text-cyan'
                }`}
              >
                {option}
              </button>
            ))}
          </div>
        </div>
      </div>

      <FileTable files={filtered} />
    </section>
  );
}
