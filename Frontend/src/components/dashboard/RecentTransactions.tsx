import { useMemo, useState } from 'react'
import { ArrowDown, ArrowUp, ArrowUpDown, ChevronLeft, ChevronRight, ExternalLink, Search, SlidersHorizontal } from 'lucide-react'
import { ProcurementTransaction, TransactionStatus, transactions } from '../../data/mockData'

type SortKey = keyof Pick<ProcurementTransaction,'id'|'supplier'|'purchaseOrder'|'amount'|'date'|'status'>
const statuses: Array<'All statuses'|TransactionStatus> = ['All statuses','Approved','Pending','Under Review','Flagged']
const formatAmount = (amount:number) => new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(amount)

export default function RecentTransactions({search:globalSearch}:{search:string}) {
  const [search,setSearch] = useState('')
  const [status,setStatus] = useState<'All statuses'|TransactionStatus>('All statuses')
  const [sortKey,setSortKey] = useState<SortKey>('date')
  const [ascending,setAscending] = useState(false)
  const [page,setPage] = useState(1)
  const pageSize=6
  const filtered = useMemo(()=>transactions.filter(row=>{
    const query=`${search} ${globalSearch}`.trim().toLowerCase()
    const matchesQuery=!query||`${row.id} ${row.supplier} ${row.purchaseOrder} ${row.amount} ${row.status}`.toLowerCase().includes(query)
    return matchesQuery&&(status==='All statuses'||row.status===status)
  }).sort((a,b)=>{
    const left=a[sortKey],right=b[sortKey]
    const comparison=typeof left==='number'&&typeof right==='number'?left-right:String(left).localeCompare(String(right))
    return ascending?comparison:-comparison
  }),[search,globalSearch,status,sortKey,ascending])
  const pageCount=Math.max(1,Math.ceil(filtered.length/pageSize))
  const currentPage=Math.min(page,pageCount)
  const currentRows=filtered.slice((currentPage-1)*pageSize,currentPage*pageSize)
  const sort = (key:SortKey) => { if(sortKey===key)setAscending(!ascending);else{setSortKey(key);setAscending(true)}setPage(1) }
  const heading = (label:string,key:SortKey) => <button className="sort-heading" onClick={()=>sort(key)}>{label}{sortKey===key?(ascending?<ArrowUp size={12}/>:<ArrowDown size={12}/>):<ArrowUpDown size={12}/>}</button>

  return <section className="dashboard-section transactions-section"><div className="dashboard-section-heading"><div><h2>Recent transactions</h2><p>Review purchase activity across your organization</p></div><button className="table-view-all" onClick={()=>{setStatus('All statuses');setSearch('');setPage(1)}}>Reset filters <ExternalLink size={13}/></button></div><div className="dashboard-panel transaction-panel"><div className="transaction-toolbar"><label className="transaction-search"><Search size={15}/><input value={search} onChange={event=>{setSearch(event.target.value);setPage(1)}} placeholder="Search transactions..." aria-label="Search transactions"/></label><label className="status-select"><SlidersHorizontal size={14}/><select value={status} onChange={event=>{setStatus(event.target.value as 'All statuses'|TransactionStatus);setPage(1)}} aria-label="Filter transactions by status">{statuses.map(item=><option key={item}>{item}</option>)}</select></label></div><div className="table-scroll"><table className="transactions-table"><thead><tr><th>{heading('Transaction ID','id')}</th><th>{heading('Supplier','supplier')}</th><th>{heading('Purchase order','purchaseOrder')}</th><th>{heading('Amount','amount')}</th><th>{heading('Date','date')}</th><th>{heading('Status','status')}</th><th><span className="sr-only">Action</span></th></tr></thead><tbody>{currentRows.map(row=><tr key={row.id}><td className="transaction-id">{row.id}</td><td><span className="supplier-cell"><i>{row.supplier.slice(0,1)}</i>{row.supplier}</span></td><td className="po-cell">{row.purchaseOrder}</td><td className="amount-cell">{formatAmount(row.amount)}</td><td className="date-cell">{new Intl.DateTimeFormat('en-US',{month:'short',day:'numeric',year:'numeric'}).format(new Date(`${row.date}T12:00:00`))}</td><td><span className={`transaction-status status-${row.status.toLowerCase().replace(/ /g,'-')}`}><i/>{row.status}</span></td><td><button className="row-action" aria-label={`View ${row.id}`} title={`View ${row.id}`} onClick={()=>window.alert(`${row.id}\n${row.supplier} · ${formatAmount(row.amount)}\nStatus: ${row.status}`)}><ExternalLink size={14}/></button></td></tr>)}</tbody></table>{currentRows.length===0&&<div className="table-empty">No transactions match these filters.</div>}</div><div className="table-footer"><span>Showing <b>{filtered.length?((currentPage-1)*pageSize)+1:0}–{Math.min(currentPage*pageSize,filtered.length)}</b> of <b>{filtered.length}</b> transactions</span><div className="pagination"><button disabled={currentPage===1} onClick={()=>setPage(Math.max(1,currentPage-1))} aria-label="Previous page"><ChevronLeft size={15}/></button><span>Page {currentPage} of {pageCount}</span><button disabled={currentPage>=pageCount} onClick={()=>setPage(Math.min(pageCount,currentPage+1))} aria-label="Next page"><ChevronRight size={15}/></button></div></div></div></section>
}
