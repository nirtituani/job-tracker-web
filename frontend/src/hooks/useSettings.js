import { useState } from 'react';

const DEFAULTS = {
  statuses: [
    'Pre-Applied', 'Applied', 'Online Assessment', 'Phone Screen',
    'Interview Round 1', 'Interview Round 2', 'Interview Round 3',
    'Final Interview', 'Offer Received', 'Rejected', 'Ghosted', 'Withdrawn',
  ],
  viaOptions: [
    'Company Website', 'LinkedIn', 'Recruiter', 'Direct Email', 'Referral', 'Headhunter',
  ],
  statusColors: {},
};

function load() {
  try {
    const stored = localStorage.getItem('jobtracker_settings');
    return stored ? { ...DEFAULTS, ...JSON.parse(stored) } : DEFAULTS;
  } catch {
    return DEFAULTS;
  }
}

export function useSettings() {
  const [settings, setSettings] = useState(load);

  const save = (next) => {
    setSettings(next);
    localStorage.setItem('jobtracker_settings', JSON.stringify(next));
  };

  const addStatus = (val) => {
    const trimmed = val.trim();
    if (!trimmed || settings.statuses.includes(trimmed)) return;
    save({ ...settings, statuses: [...settings.statuses, trimmed] });
  };

  const removeStatus = (val) => {
    const { [val]: _, ...rest } = settings.statusColors;
    save({ ...settings, statuses: settings.statuses.filter(s => s !== val), statusColors: rest });
  };

  const addVia = (val) => {
    const trimmed = val.trim();
    if (!trimmed || settings.viaOptions.includes(trimmed)) return;
    save({ ...settings, viaOptions: [...settings.viaOptions, trimmed] });
  };

  const removeVia = (val) => {
    save({ ...settings, viaOptions: settings.viaOptions.filter(v => v !== val) });
  };

  const setStatusColor = (status, color) => {
    save({ ...settings, statusColors: { ...settings.statusColors, [status]: color } });
  };

  return { settings, addStatus, removeStatus, addVia, removeVia, setStatusColor };
}
