const STORAGE_KEY = 'procuremind-workspace-settings-v1';

export const DEFAULT_WORKSPACE_SETTINGS = {
  workspaceName: 'Acme Corporation',
  timezone: 'Asia/Makassar',
  currency: 'USD',
  dateFormat: 'DD MMM YYYY',
  defaultModule: '/dashboard',
  approvalThreshold: '50000',
  compactTables: false,
  criticalAlerts: true,
  approvalNotifications: true,
  weeklyDigest: false,
  sessionTimeout: '30',
};

export function getWorkspaceSettings() {
  try {
    const stored = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || '{}');
    return { ...DEFAULT_WORKSPACE_SETTINGS, ...(stored && typeof stored === 'object' ? stored : {}) };
  } catch {
    return { ...DEFAULT_WORKSPACE_SETTINGS };
  }
}

export function saveWorkspaceSettings(settings) {
  const next = { ...DEFAULT_WORKSPACE_SETTINGS, ...settings };
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  window.dispatchEvent(new CustomEvent('procuremind:settings-updated'));
  return next;
}

export function resetWorkspaceSettings() {
  window.localStorage.removeItem(STORAGE_KEY);
  window.dispatchEvent(new CustomEvent('procuremind:settings-updated'));
  return { ...DEFAULT_WORKSPACE_SETTINGS };
}
