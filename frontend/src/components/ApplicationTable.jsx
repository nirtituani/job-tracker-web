import { Search, Filter, Download, Trash2, Edit2, FileText, XCircle, RotateCcw } from 'lucide-react';
import StatusBadge from './StatusBadge';

const BUILTIN_ACTIVE = new Set([
  'Applied', 'Phone Screen', 'Online Assessment',
  'Interview Round 1', 'Interview Round 2', 'Interview Round 3',
  'Final Interview', 'Offer Received',
]);
const GREEN_COLORS = new Set(['green', 'emerald']);
const MUTED_COLORS = new Set(['gray', 'red']);

function rowColor(app, statusColors) {
  if (app.rejected || app.status === 'Rejected' || app.status === 'Ghosted' || app.status === 'Withdrawn')
    return 'bg-muted/50 hover:bg-muted/70 opacity-60';
  const custom = statusColors?.[app.status];
  if (custom) {
    if (GREEN_COLORS.has(custom)) return 'bg-green-50 hover:bg-green-100/70';
    if (MUTED_COLORS.has(custom)) return 'bg-muted/50 hover:bg-muted/70 opacity-60';
    return 'hover:bg-muted/30';
  }
  if (BUILTIN_ACTIVE.has(app.status)) return 'bg-green-50 hover:bg-green-100/70';
  return 'hover:bg-muted/30';
}

export default function ApplicationTable({ applications, search, setSearch, statusFilter, setStatusFilter, onExport, onEdit, onDelete, onToggleReject, statuses, statusColors }) {
  const STATUSES = ['All', ...statuses];
  return (
    <div className="bg-card rounded-xl border border-border overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="relative flex-1 max-w-xs">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input type="text" placeholder="Search applications..." value={search} onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-background border border-border rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" />
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Filter size={14} className="text-muted-foreground" />
            <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
              className="bg-background border border-border rounded-full px-3 py-2 text-sm focus:outline-none">
              {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <button onClick={onExport} className="flex items-center gap-2 px-4 py-2 border border-border rounded-full text-sm hover:bg-muted transition-colors">
            <Download size={14} /> Export CSV
          </button>
        </div>
      </div>
      <table className="w-full">
        <thead>
          <tr className="border-b border-border">
            {['Company', 'Job Title', 'Status', 'Date Applied', 'Match', 'Applied Via', 'Job Desc', ''].map(h => (
              <th key={h} className="px-4 py-3 text-left text-xs font-primary font-medium text-muted-foreground">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {applications.length === 0 ? (
            <tr><td colSpan={8} className="text-center py-12 text-muted-foreground">No applications found</td></tr>
          ) : applications.map(app => (
            <tr key={app.id} className={`border-b border-border transition-colors ${rowColor(app, statusColors)}`}>
              <td className="px-4 py-3 text-sm font-medium">{app.company}</td>
              <td className="px-4 py-3 text-sm text-muted-foreground">{app.title}</td>
              <td className="px-4 py-3">
                <StatusBadge status={app.status} customColor={statusColors?.[app.status]} />
              </td>
              <td className="px-4 py-3 text-sm text-muted-foreground">{app.date_applied}</td>
              <td className="px-4 py-3 text-sm text-muted-foreground">{app.match_rating ? `${app.match_rating * 20}%` : '-'}</td>
              <td className="px-4 py-3 text-sm text-muted-foreground">{app.applied_via}</td>
              <td className="px-4 py-3">
                {app.job_desc_link
                  ? <a href={app.job_desc_link} target="_blank" rel="noopener noreferrer"
                      className="text-primary hover:text-primary/70 transition-colors" title="View job description">
                      <FileText size={15} />
                    </a>
                  : <span className="text-muted-foreground/30"><FileText size={15} /></span>}
              </td>
              <td className="px-4 py-3">
                <div className="flex gap-1">
                  <button onClick={() => onEdit(app)} className="p-1.5 rounded-lg hover:bg-muted transition-colors text-muted-foreground hover:text-foreground" title="Edit">
                    <Edit2 size={14} />
                  </button>
                  <button
                    onClick={() => onToggleReject(app)}
                    title={app.rejected ? 'Undo rejection' : 'Mark as rejected'}
                    className={`p-1.5 rounded-lg transition-colors ${app.rejected ? 'text-orange-400 hover:bg-orange-50 hover:text-orange-500' : 'text-muted-foreground hover:bg-red-50 hover:text-red-500'}`}>
                    {app.rejected ? <RotateCcw size={14} /> : <XCircle size={14} />}
                  </button>
                  <button onClick={() => onDelete(app.id)} className="p-1.5 rounded-lg hover:bg-red-50 transition-colors text-muted-foreground hover:text-red-500" title="Delete">
                    <Trash2 size={14} />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
