import { LayoutDashboard, FileText, BarChart3, Settings, LogOut } from 'lucide-react';

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard' },
  { icon: FileText, label: 'Applications' },
  { icon: BarChart3, label: 'Analytics' },
  { icon: Settings, label: 'Settings' },
];

export default function Sidebar({ activeView, setActiveView, user, onLogout }) {
  return (
    <aside className="w-[240px] min-h-screen bg-sidebar border-r border-sidebar-border flex flex-col">
      <div className="h-[72px] flex items-center gap-2 px-6 border-b border-sidebar-border">
        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
          <span className="text-white font-bold text-sm">JT</span>
        </div>
        <span className="font-primary font-bold text-base text-foreground">JOBTRACKER</span>
      </div>
      <nav className="flex-1 py-4 px-3">
        <p className="text-xs font-medium text-muted-foreground px-3 mb-2 uppercase tracking-wider">Navigation</p>
        {navItems.map(({ icon: Icon, label }) => (
          <button key={label} onClick={() => setActiveView(label)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm mb-1 transition-colors ${
              activeView === label ? 'bg-sidebar-accent text-foreground font-medium' : 'text-muted-foreground hover:bg-sidebar-accent/50'
            }`}>
            <Icon size={18} />
            {label}
          </button>
        ))}
      </nav>
      <div className="px-4 py-4 border-t border-sidebar-border">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-primary/20 flex items-center justify-center text-sm font-semibold text-primary">
            {user?.email?.[0]?.toUpperCase() ?? 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground truncate">{user?.email ?? ''}</p>
          </div>
          <button onClick={onLogout} title="Logout"
            className="text-muted-foreground hover:text-red-500 transition-colors flex-shrink-0">
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  );
}
