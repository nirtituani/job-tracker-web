const statusColors = {
  'Applied': 'bg-green-100 text-green-700',
  'Pre-Applied': 'bg-orange-100 text-orange-700',
  'Online Assessment': 'bg-blue-100 text-blue-700',
  'Phone Screen': 'bg-green-100 text-green-700',
  'Interview Round 1': 'bg-violet-100 text-violet-700',
  'Interview Round 2': 'bg-violet-100 text-violet-700',
  'Interview Round 3': 'bg-violet-100 text-violet-700',
  'Final Interview': 'bg-violet-100 text-violet-700',
  'Offer Received': 'bg-emerald-100 text-emerald-800',
  'Rejected': 'bg-gray-100 text-gray-600',
  'Ghosted': 'bg-gray-100 text-gray-500',
  'Withdrawn': 'bg-yellow-100 text-yellow-700',
};

export default function StatusBadge({ status }) {
  const colors = statusColors[status] || 'bg-gray-100 text-gray-600';
  return (
    <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${colors}`}>
      {status}
    </span>
  );
}
