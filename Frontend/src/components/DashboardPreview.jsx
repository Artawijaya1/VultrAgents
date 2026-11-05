import { motion } from 'framer-motion';
import { Activity, ShieldCheck, Zap } from 'lucide-react';

export default function DashboardPreview() {
  return <motion.div className="dashboard-wrap" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .7, delay: .15 }}>
    <div className="float-badge approval"><span className="badge-icon green"><ShieldCheck size={15} /></span><span><b>Verified</b><small>Database records</small></span></div>
    <div className="dashboard"><div className="dash-top"><div className="window-dots"><i /><i /><i /></div><span>PROCUREMIND DASHBOARD</span></div>
      <div className="kpi-grid"><div className="kpi"><strong>—</strong><span>Total Spend</span><div className="progress"><i style={{ width: '0%' }} /></div></div><div className="kpi"><strong>—</strong><span>Suppliers</span><div className="progress"><i style={{ width: '0%' }} /></div></div></div>
      <div className="chart-panel"><div className="chart-heading"><span>Procurement analytics</span><span>Sign in to load database records</span></div><div className="hero-chart preview-empty"><Activity size={22} /><span>Live dashboard data</span></div></div>
    </div>
    <div className="float-badge ai-status"><span className="badge-icon"><Zap size={16} /></span><span><b>AI insights</b><small>Based on your data</small></span></div>
  </motion.div>;
}
