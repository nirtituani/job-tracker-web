import { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import StatsCards from './components/StatsCards';
import ApplicationTable from './components/ApplicationTable';
import AddApplicationModal from './components/AddApplicationModal';
import AuthPage from './pages/AuthPage';
import { getApplications, getStats, addApplication, updateApplication, deleteApplication, exportCsv } from './api/applications';
import { getMe, logout as apiLogout } from './api/auth';
import { useSettings } from './hooks/useSettings';
import { Plus, X } from 'lucide-react';

function TagList({ label, items, onAdd, onRemove }) {
  const [input, setInput] = useState('');
  const submit = () => { onAdd(input); setInput(''); };
  return (
    <div>
      <label className="block text-sm font-medium mb-2">{label}</label>
      <div className="flex flex-wrap gap-2 mb-3">
        {items.map(item => (
          <span key={item} className="flex items-center gap-1.5 px-3 py-1 bg-muted border border-border rounded-full text-sm">
            {item}
            <button onClick={() => onRemove(item)} className="text-muted-foreground hover:text-red-500 transition-colors">
              <X size={12} />
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && submit()}
          placeholder={`Add new ${label.toLowerCase().replace(' options', '')}...`}
          className="flex-1 px-4 py-2 bg-background border border-border rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
        />
        <button onClick={submit} className="px-4 py-2 bg-primary text-white rounded-full text-sm font-medium hover:bg-primary/90 transition-colors">
          Add
        </button>
      </div>
    </div>
  );
}

function SettingsView({ settings, addStatus, removeStatus, addVia, removeVia }) {
  return (
    <div className="space-y-6 max-w-lg">
      <h1 className="text-2xl font-primary font-bold">Settings</h1>
      <div className="bg-card rounded-xl border border-border p-6 space-y-6">
        <TagList label="Status Options" items={settings.statuses} onAdd={addStatus} onRemove={removeStatus} />
        <div className="border-t border-border" />
        <TagList label="Applied Via Options" items={settings.viaOptions} onAdd={addVia} onRemove={removeVia} />
      </div>
    </div>
  );
}

function AnalyticsView({ stats, apps }) {
  const byStatus = apps.reduce((acc, a) => { acc[a.status] = (acc[a.status] || 0) + 1; return acc; }, {});
  const responseRate = stats.total > 0 ? Math.round(((stats.active + stats.interviews) / stats.total) * 100) : 0;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-primary font-bold">Analytics</h1>
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-card rounded-xl border border-border p-6">
          <h2 className="text-sm font-medium text-muted-foreground mb-4">Applications by Status</h2>
          <div className="space-y-3">
            {Object.entries(byStatus).sort((a, b) => b[1] - a[1]).map(([status, count]) => (
              <div key={status} className="flex items-center justify-between">
                <span className="text-sm text-foreground">{status}</span>
                <div className="flex items-center gap-3">
                  <div className="w-32 h-2 bg-muted rounded-full overflow-hidden">
                    <div className="h-full bg-primary rounded-full" style={{ width: `${(count / stats.total) * 100}%` }} />
                  </div>
                  <span className="text-sm font-medium w-4 text-right">{count}</span>
                </div>
              </div>
            ))}
            {Object.keys(byStatus).length === 0 && <p className="text-muted-foreground text-sm">No data yet</p>}
          </div>
        </div>
        <div className="bg-card rounded-xl border border-border p-6 space-y-5">
          <h2 className="text-sm font-medium text-muted-foreground mb-4">Summary</h2>
          {[
            { label: 'Total Applications', value: stats.total },
            { label: 'Active / In Progress', value: stats.active },
            { label: 'Interviews Secured', value: stats.interviews },
            { label: 'Rejected', value: stats.rejected },
            { label: 'Response Rate', value: `${responseRate}%` },
          ].map(({ label, value }) => (
            <div key={label} className="flex justify-between items-center border-b border-border pb-3 last:border-0 last:pb-0">
              <span className="text-sm text-muted-foreground">{label}</span>
              <span className="text-sm font-primary font-semibold">{value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState(undefined);
  const [apps, setApps] = useState([]);
  const [stats, setStats] = useState({ total: 0, active: 0, interviews: 0, rejected: 0 });
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [modalOpen, setModalOpen] = useState(false);
  const [editData, setEditData] = useState(null);
  const [activeView, setActiveView] = useState('Dashboard');
  const { settings, addStatus, removeStatus, addVia, removeVia } = useSettings();

  useEffect(() => { getMe().then(setUser); }, []);

  const handleLogout = async () => {
    await apiLogout();
    setUser(null);
  };

  const refresh = useCallback(async () => {
    const [a, s] = await Promise.all([getApplications(search, statusFilter), getStats()]);
    setApps(a);
    setStats(s);
  }, [search, statusFilter]);

  useEffect(() => {
    if (user) refresh();
  }, [refresh, user]);

  const handleSave = async (form) => {
    if (editData) {
      const updated = await updateApplication(editData.id, form);
      setApps(prev => prev.map(a => a.id === editData.id ? updated : a));
    } else {
      const created = await addApplication(form);
      setApps(prev => [created, ...prev]);
    }
    setModalOpen(false);
    setEditData(null);
    getStats().then(setStats);
  };

  const handleEdit = (app) => { setEditData(app); setModalOpen(true); };
  const handleDelete = async (id) => {
    if (confirm('Delete this application?')) {
      await deleteApplication(id);
      setApps(prev => prev.filter(a => a.id !== id));
      getStats().then(setStats);
    }
  };

  if (user === undefined) return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <p className="text-muted-foreground text-sm">Loading...</p>
    </div>
  );
  if (user === null) return <AuthPage onAuth={setUser} />;

  const renderMain = () => {
    if (activeView === 'Analytics') return <AnalyticsView stats={stats} apps={apps} />;
    if (activeView === 'Settings') return (
      <SettingsView settings={settings} addStatus={addStatus} removeStatus={removeStatus} addVia={addVia} removeVia={removeVia} />
    );
    const isDashboard = activeView === 'Dashboard';
    return (
      <>
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-primary font-bold">{activeView}</h1>
          <button onClick={() => { setEditData(null); setModalOpen(true); }}
            className="flex items-center gap-2 px-5 py-2.5 bg-primary text-white rounded-full text-sm font-primary font-medium hover:bg-primary/90 transition-colors">
            <Plus size={18} /> Add Application
          </button>
        </div>
        <div className="space-y-6">
          {isDashboard && <StatsCards stats={stats} />}
          <ApplicationTable applications={apps} search={search} setSearch={setSearch}
            statusFilter={statusFilter} setStatusFilter={setStatusFilter}
            onExport={exportCsv} onEdit={handleEdit} onDelete={handleDelete}
            statuses={settings.statuses} />
        </div>
      </>
    );
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar activeView={activeView} setActiveView={setActiveView} user={user} onLogout={handleLogout} />
      <main className="flex-1 p-8">{renderMain()}</main>
      <AddApplicationModal isOpen={modalOpen} onClose={() => { setModalOpen(false); setEditData(null); }}
        onSave={handleSave} editData={editData}
        statuses={settings.statuses} viaOptions={settings.viaOptions} />
    </div>
  );
}
