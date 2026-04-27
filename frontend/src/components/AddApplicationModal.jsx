import { X } from 'lucide-react';
import { useState, useEffect } from 'react';

const today = new Date().toLocaleDateString('en-GB').replace(/\//g, '/');

export default function AddApplicationModal({ isOpen, onClose, onSave, editData, statuses, viaOptions }) {
  const emptyForm = {
    company: '', title: '', location: '', date_applied: today,
    status: statuses[0] || 'Pre-Applied',
    salary_range: '', job_link: '', contact_person: '', contact_email: '',
    applied_via: '',
    match_rating: 0, notes: '',
  };
  const [form, setForm] = useState(emptyForm);
  const isEdit = !!editData;

  useEffect(() => {
    setForm(editData ? { ...emptyForm, ...editData } : emptyForm);
  }, [editData, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.company || !form.title) return;
    onSave(form);
  };

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center py-4 bg-black/40" onClick={onClose}>
      <form onClick={e => e.stopPropagation()} onSubmit={handleSubmit}
        className="bg-card w-[560px] rounded-2xl border border-border shadow-2xl overflow-hidden flex flex-col max-h-[95vh]">
        <div className="flex items-center justify-between px-6 py-4 border-b border-border flex-shrink-0">
          <div>
            <h2 className="text-lg font-primary font-semibold">{isEdit ? 'Edit Application' : 'Add New Application'}</h2>
            <p className="text-sm text-muted-foreground font-secondary">{isEdit ? 'Update application details' : 'Track a new job application'}</p>
          </div>
          <button type="button" onClick={onClose} className="text-muted-foreground hover:text-foreground"><X size={20} /></button>
        </div>
        <div className="p-4 grid grid-cols-2 gap-3 overflow-y-auto">
          <Field label="Company Name *" value={form.company} onChange={v => set('company', v)} placeholder="e.g. Google" />
          <Field label="Job Title *" value={form.title} onChange={v => set('title', v)} placeholder="e.g. Software Engineer" />
          <Field label="Location" value={form.location} onChange={v => set('location', v)} placeholder="e.g. Tel Aviv" />
          <Field label="Date Applied" value={form.date_applied} onChange={v => set('date_applied', v)} placeholder="DD/MM/YYYY" />
          <SelectField label="Status" value={form.status} onChange={v => set('status', v)} options={statuses} />
          <Field label="Salary Range" value={form.salary_range} onChange={v => set('salary_range', v)} placeholder="e.g. 30K-40K" />
          <Field label="Job Link" value={form.job_link} onChange={v => set('job_link', v)} placeholder="https://..." />
          <Field label="Contact Person" value={form.contact_person} onChange={v => set('contact_person', v)} placeholder="e.g. Jane Smith" />
          <Field label="Contact Email" value={form.contact_email} onChange={v => set('contact_email', v)} placeholder="email@company.com" />
          <SelectField label="Applied Via" value={form.applied_via} onChange={v => set('applied_via', v)} options={['', ...viaOptions]} labels={['Select...', ...viaOptions]} />
          <SelectField label="Job Match (1-5)" value={form.match_rating} onChange={v => set('match_rating', Number(v))}
            options={[0,1,2,3,4,5]} labels={['Select...','1','2','3','4','5']} />
          <div />
          <div className="col-span-2">
            <label className="block text-sm font-medium mb-1.5">Notes</label>
            <textarea value={form.notes} onChange={e => set('notes', e.target.value)} placeholder="Add any notes..."
              className="w-full px-4 py-3 bg-background border border-border rounded-2xl text-sm resize-none h-20 focus:outline-none focus:ring-2 focus:ring-primary/30" />
          </div>
        </div>
        <div className="flex justify-end gap-3 px-6 py-4 border-t border-border flex-shrink-0">
          <button type="button" onClick={onClose}
            className="px-4 py-2.5 border border-border rounded-full text-sm font-primary font-medium hover:bg-muted transition-colors">Cancel</button>
          <button type="submit"
            className="px-5 py-2.5 bg-primary text-white rounded-full text-sm font-primary font-medium hover:bg-primary/90 transition-colors">
            {isEdit ? 'Save Changes' : 'Add Application'}
          </button>
        </div>
      </form>
    </div>
  );
}

function Field({ label, value, onChange, placeholder }) {
  return (
    <div>
      <label className="block text-sm font-medium mb-1.5">{label}</label>
      <input type="text" value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
        className="w-full px-4 py-2.5 bg-background border border-border rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" />
    </div>
  );
}

function SelectField({ label, value, onChange, options, labels }) {
  return (
    <div>
      <label className="block text-sm font-medium mb-1.5">{label}</label>
      <select value={value} onChange={e => onChange(e.target.value)}
        className="w-full px-4 py-2.5 bg-background border border-border rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 appearance-none">
        {options.map((o, i) => <option key={o} value={o}>{labels ? labels[i] : o}</option>)}
      </select>
    </div>
  );
}
