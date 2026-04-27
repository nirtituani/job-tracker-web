export const COLOR_OPTIONS = [
  { key: 'green',   badge: 'bg-green-100 text-green-700',     dot: 'bg-green-400' },
  { key: 'blue',    badge: 'bg-blue-100 text-blue-700',       dot: 'bg-blue-400' },
  { key: 'violet',  badge: 'bg-violet-100 text-violet-700',   dot: 'bg-violet-400' },
  { key: 'orange',  badge: 'bg-orange-100 text-orange-700',   dot: 'bg-orange-400' },
  { key: 'yellow',  badge: 'bg-yellow-100 text-yellow-700',   dot: 'bg-yellow-400' },
  { key: 'emerald', badge: 'bg-emerald-100 text-emerald-800', dot: 'bg-emerald-400' },
  { key: 'pink',    badge: 'bg-pink-100 text-pink-700',       dot: 'bg-pink-400' },
  { key: 'red',     badge: 'bg-red-100 text-red-600',         dot: 'bg-red-400' },
  { key: 'gray',    badge: 'bg-gray-100 text-gray-600',       dot: 'bg-gray-400' },
];

const BUILTIN_COLORS = {
  'Applied':           'bg-green-100 text-green-700',
  'Pre-Applied':       'bg-orange-100 text-orange-700',
  'Online Assessment': 'bg-blue-100 text-blue-700',
  'Phone Screen':      'bg-green-100 text-green-700',
  'Interview Round 1': 'bg-violet-100 text-violet-700',
  'Interview Round 2': 'bg-violet-100 text-violet-700',
  'Interview Round 3': 'bg-violet-100 text-violet-700',
  'Final Interview':   'bg-violet-100 text-violet-700',
  'Offer Received':    'bg-emerald-100 text-emerald-800',
  'Rejected':          'bg-gray-100 text-gray-600',
  'Ghosted':           'bg-gray-100 text-gray-500',
  'Withdrawn':         'bg-yellow-100 text-yellow-700',
};

export default function StatusBadge({ status, customColor }) {
  let classes;
  if (customColor) {
    const opt = COLOR_OPTIONS.find(c => c.key === customColor);
    classes = opt ? opt.badge : 'bg-gray-100 text-gray-600';
  } else {
    classes = BUILTIN_COLORS[status] || 'bg-gray-100 text-gray-600';
  }
  return (
    <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${classes}`}>
      {status}
    </span>
  );
}
