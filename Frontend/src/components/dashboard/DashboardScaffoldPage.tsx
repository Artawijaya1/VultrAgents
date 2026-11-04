import { Link, useOutletContext, useParams } from 'react-router-dom'
import { ArrowRight, FileSearch, Settings2, ShieldCheck, Users } from 'lucide-react'
import { DashboardOutletContext } from '../../types/dashboard'

const pages = {
  'purchase-orders': { title:'Purchase Orders', description:'Track purchase requests and order progress across the organization.', icon:FileSearch },
  suppliers: { title:'Suppliers', description:'Review supplier records, performance, and relationship details.', icon:Users },
  invoices: { title:'Invoices & Contracts', description:'A consolidated workspace for invoice and contract review.', icon:FileSearch },
  'audit-logs': { title:'Audit Logs', description:'A clear view of procurement actions and review history.', icon:ShieldCheck },
  settings: { title:'Workspace Settings', description:'Manage workspace preferences and team configuration.', icon:Settings2 },
}

export default function DashboardScaffoldPage() {
  const { section } = useParams<{section:keyof typeof pages}>()
  const { search } = useOutletContext<DashboardOutletContext>()
  const page = section ? pages[section] : undefined
  if (!page) return null
  const Icon=page.icon
  return <div className="dashboard-scaffold"><div className="dashboard-eyebrow"><span className="live-dot"/> PROCUREMENT WORKSPACE</div><div className="scaffold-title"><span><h1>{page.title}</h1><p>{page.description}</p></span><span className="scaffold-icon"><Icon size={22}/></span></div><div className="scaffold-placeholder"><span className="scaffold-placeholder-icon"><Icon size={22}/></span><h2>{page.title} workspace</h2><p>This section is prepared for the next product phase. No live procurement records are connected yet.</p>{search&&<small>Dashboard search: “{search}”</small>}<Link className="dashboard-text-link" to="/dashboard">Return to overview <ArrowRight size={14}/></Link></div></div>
}
