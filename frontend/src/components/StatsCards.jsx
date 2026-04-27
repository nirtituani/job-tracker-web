import { Briefcase, TrendingUp, Users, XCircle } from 'lucide-react';

const cards = [
  { key: 'total', label: 'Total Applications', icon: Briefcase, color: 'text-primary bg-orange-50' },
  { key: 'active', label: 'Active', icon: TrendingUp, color: 'text-green-600 bg-green-50' },
  { key: 'interviews', label: 'Interviews', icon: Users, color: 'text-violet-600 bg-violet-50' },
  { key: 'rejected', label: 'Rejected', icon: XCircle, color: 'text-gray-500 bg-gray-100' },
];

export default function StatsCards({ stats }) {
  return (
    <div className="grid grid-cols-4 gap-4">
      {cards.map(({ key, label, icon: Icon, color }) => (
        <div key={key} className="bg-card rounded-xl border border-border p-5 flex items-center gap-4">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
            <Icon size={20} />
          </div>
          <div>
            <p className="text-2xl font-primary font-bold text-foreground">{stats[key] ?? 0}</p>
            <p className="text-xs text-muted-foreground font-secondary">{label}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
