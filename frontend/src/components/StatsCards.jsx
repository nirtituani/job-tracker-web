import { Briefcase, TrendingUp, Users, XCircle } from 'lucide-react';

const cards = [
  { key: 'total', label: 'Total Applications', icon: Briefcase,
    gradient: 'from-orange-500/10 to-amber-500/5',
    iconBg: 'bg-gradient-to-br from-orange-500 to-amber-500',
    glow: 'shadow-orange-500/20',
    ring: 'ring-orange-400' },
  { key: 'active', label: 'Active', icon: TrendingUp,
    gradient: 'from-emerald-500/10 to-green-500/5',
    iconBg: 'bg-gradient-to-br from-emerald-500 to-green-500',
    glow: 'shadow-emerald-500/20',
    ring: 'ring-emerald-400' },
  { key: 'interviews', label: 'Interviews', icon: Users,
    gradient: 'from-violet-500/10 to-purple-500/5',
    iconBg: 'bg-gradient-to-br from-violet-500 to-purple-500',
    glow: 'shadow-violet-500/20',
    ring: 'ring-violet-400' },
  { key: 'rejected', label: 'Rejected', icon: XCircle,
    gradient: 'from-slate-500/10 to-gray-500/5',
    iconBg: 'bg-gradient-to-br from-slate-500 to-gray-500',
    glow: 'shadow-slate-500/20',
    ring: 'ring-slate-400' },
];

export default function StatsCards({ stats, activeFilter, onFilter }) {
  return (
    <div className="grid grid-cols-4 gap-4">
      {cards.map(({ key, label, icon: Icon, gradient, iconBg, glow, ring }) => {
        const isActive = activeFilter === key;
        return (
          <button key={key} onClick={() => onFilter(key)}
            className={`relative overflow-hidden bg-gradient-to-br ${gradient}
              border rounded-2xl p-5 flex items-center gap-4 w-full text-left
              hover:scale-[1.02] hover:shadow-lg transition-all duration-300
              ${isActive ? `ring-2 ${ring} border-transparent shadow-lg scale-[1.02]` : 'border-white/60'}`}>
            <div className={`absolute -top-8 -right-8 w-24 h-24 rounded-full ${iconBg} opacity-10 blur-2xl`} />
            <div className={`w-12 h-12 rounded-xl ${iconBg} shadow-lg ${glow} flex items-center justify-center shrink-0`}>
              <Icon size={22} className="text-white" />
            </div>
            <div>
              <p className="text-3xl font-mono font-bold text-gray-900 tracking-tight">{stats[key] ?? 0}</p>
              <p className="text-xs text-gray-500 mt-0.5">{label}</p>
            </div>
          </button>
        );
      })}
    </div>
  );
}
