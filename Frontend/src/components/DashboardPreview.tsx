import { motion } from 'framer-motion'
import { Activity, ArrowUpRight, Zap } from 'lucide-react'
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis } from 'recharts'
import { monthlySpend } from '../data/mockData'

export default function DashboardPreview() {
  return <motion.div className="dashboard-wrap" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .7, delay: .15 }}>
    <div className="float-badge approval"><span className="badge-icon green"><Activity size={15} /></span><span><b>98.5%</b><small>Approval Rate</small></span></div>
    <div className="dashboard">
      <div className="dash-top"><div className="window-dots"><i/><i/><i/></div><span>PROCUREMIND DASHBOARD</span></div>
      <div className="kpi-grid">
        <div className="kpi"><strong>$2.4M</strong><span>Total Spend</span><div className="progress"><i style={{width:'74%'}} /></div></div>
        <div className="kpi"><strong>847</strong><span>Active Vendors</span><div className="progress"><i style={{width:'67%'}} /></div></div>
      </div>
      <div className="chart-panel"><div className="chart-heading"><span>Monthly Procurement Analytics</span><span>Demo data</span></div><div className="hero-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={monthlySpend} barCategoryGap="17%"><XAxis dataKey="month" hide /><Tooltip cursor={false} contentStyle={{ background:'#101827',border:'1px solid #26364b',borderRadius:8,color:'#e8f0fa',fontSize:12 }} formatter={(value) => [`$${value}k`, 'Spend']} /><Bar dataKey="spend" fill="#22b9ef" radius={[3,3,0,0]} /></BarChart></ResponsiveContainer></div></div>
    </div>
    <div className="float-badge ai-status"><span className="badge-icon"><Zap size={16} /></span><span><b>AI Active</b><small>Monitoring activity</small></span></div>
    <span className="dashboard-spark"><ArrowUpRight size={19}/></span>
  </motion.div>
}
