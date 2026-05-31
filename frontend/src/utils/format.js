export function truncateAddress(address = '') {
  if (!address || address.length < 12) return address;
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

export function formatBytes(bytes = 0) {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = Number(bytes);
  let index = 0;
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024;
    index += 1;
  }
  return `${size.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

export function formatDate(value) {
  if (!value) return 'UNKNOWN';
  return new Intl.DateTimeFormat('en', {
    month: 'short',
    day: '2-digit',
    year: 'numeric'
  }).format(new Date(value));
}

export function fileToViewModel(file) {
  return {
    id: String(file.file_id),
    fileId: file.file_id,
    name: file.original_filename,
    size: formatBytes(file.file_size),
    rawSize: file.file_size,
    timestamp: formatDate(file.created_at),
    createdAt: file.created_at,
    algorithm: file.algorithm,
    sensitivity: file.sensitivity,
    accessStatus: 'OWNER',
    ipfsHash: file.ipfs_hash,
    txHash: file.tx_hash,
    ownerWallet: file.owner_wallet
  };
}
