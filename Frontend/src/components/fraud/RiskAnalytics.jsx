import { Activity, PieChart as PieIcon, TrendingUp, ShieldCheck } from 'lucide-react';
import { Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

function EmptyChart({ message }) {
  return <div className="fraud-chart-empty"><ShieldCheck size={27} /><strong>No recorded alerts in this view</strong><span>{message}</span></div>;
}

export default function RiskAnalytics({ trend = [], distribution = [] }) {
  const total = distribution.reduce((sum, item) => sum + Number(item.count || 0), 0);
  const hasTrend = trend.some(item => Number(item.alerts || 0) > 0);
  const hasDistribution = total > 0;
  return <section className="fraud-analytics-section">
    <div className="fraud-section-title">
      <div><span className="fraud-kicker">RISK ANALYTICS</span><h2>Detection patterns</h2><p>Recent alert activity from your procurement workspace.</p></div>
      <span className="fraud-period"><Activity size={16}/> Last 14 days</span>
    </div>
    <div className="fraud-charts-grid">
      <article className="fraud-chart-card">
        <div className="fraud-chart-head"><div><h3>Suspicious transaction trend</h3><p>Recorded alerts by day</p></div><span className="fraud-chart-icon"><TrendingUp size={20}/></span></div>
        {hasTrend ? <div className="fraud-trend-chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={trend} margin={{ top: 14, right: 10, bottom: 0, left: -15 }}>
          <XAxis dataKey="date" tick={{ fill: '#a6bacd', fontSize: 12 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
          <YAxis allowDecimals={false} tick={{ fill: '#a6bacd', fontSize: 12 }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={{ background: '#101827', border: '1px solid #26364b', borderRadius: 9, color: '#e8f0fa', fontSize: 13 }} formatter={value => [value, 'Alerts']}/>
          <Line type="monotone" dataKey="alerts" name="Alerts" stroke="#31cde8" strokeWidth={3} activeDot={{ r: 5, fill: '#31cde8', stroke: '#e5faff', strokeWidth: 2 }} dot={{ r: 3, fill: '#31cde8', strokeWidth: 0 }}/>
        </LineChart></ResponsiveContainer></div> : <EmptyChart message="The database has not returned a trend of recorded alerts for this period." />}
      </article>
      <article className="fraud-chart-card anomaly-chart-card">
        <div className="fraud-chart-head"><div><h3>Anomaly distribution</h3><p>Recorded review signals by category</p></div><span className="fraud-chart-icon"><PieIcon size={20}/></span></div>
        {hasDistribution ? <div className="fraud-donut-content"><div className="fraud-donut">
          <ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={distribution} dataKey="count" nameKey="type" innerRadius={49} outerRadius={67} paddingAngle={3} stroke="none">
            {distribution.map(item => <Cell key={item.type} fill={item.color}/>)}
          </Pie><Tooltip contentStyle={{ background: '#101827', border: '1px solid #26364b', borderRadius: 8, color: '#e8f0fa', fontSize: 13 }} formatter={(value,name) => [value,name]}/></PieChart></ResponsiveContainer>
          <div className="fraud-donut-total"><b>{total}</b><small>Total alerts</small></div>
        </div><div className="fraud-anomaly-legend">{distribution.map(item => <div key={item.type}><i style={{ background: item.color }}/><span>{item.type}</span><b>{item.count}<small>{total ? `${Math.round(Number(item.count) / total * 100)}%` : '0%'}</small></b></div>)}</div></div>
          : <EmptyChart message="No persisted alert categories are available. An Agent precheck can still surface review indicators without creating dashboard alerts."/>}
      </article>
    </div>
  </section>;
}
