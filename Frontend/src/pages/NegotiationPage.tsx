import { Dispatch, SetStateAction, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, FilePlus2, Handshake, History, Sparkles } from 'lucide-react'
import AIRecommendationPanel from '../components/negotiation/AIRecommendationPanel'
import ApprovalPanel from '../components/negotiation/ApprovalPanel'
import HistoricalAnalysis from '../components/negotiation/HistoricalAnalysis'
import NegotiationComposer from '../components/negotiation/NegotiationComposer'
import NegotiationHistory from '../components/negotiation/NegotiationHistory'
import { NegotiationStrategies, NegotiationStrategy } from '../components/negotiation/NegotiationStrategyCard'
import { ProcurementContext, formatMoney, unitLabel } from '../components/negotiation/NegotiationContext'
import { negotiationPurchaseOrders, negotiationSuppliers } from '../data/negotiationData'
import { analyzeNegotiation, generateNegotiationDraft, getNegotiationHistory } from '../services/negotiationService'
import { ApprovalAction, CommunicationLanguage, CommunicationTone, NegotiationAnalysis, NegotiationInputs, NegotiationStrategyId, PurchaseOrder, ReviewStatus, Supplier } from '../types/negotiation'
import './negotiation.css'

const makeInputs=(order:PurchaseOrder):NegotiationInputs=>({purchaseOrderId:order.id,offeredUnitPrice:order.currentOffer,requestedQuantity:order.quantity,proposedDeliveryDate:order.offeredDeliveryDate,targetUnitPrice:order.targetPrice,preferredDeliveryDate:order.preferredDeliveryDate,notes:''})

export default function NegotiationPage() {
  const [supplier,setSupplier]=useState<Supplier>(negotiationSuppliers[0])
  const [order,setOrder]=useState<PurchaseOrder>(negotiationPurchaseOrders[0])
  const [inputs,setInputs]=useState<NegotiationInputs>(()=>makeInputs(negotiationPurchaseOrders[0]))
  const [analysis,setAnalysis]=useState<NegotiationAnalysis|null>(null)
  const [analysisLoading,setAnalysisLoading]=useState(false)
  const [analysisError,setAnalysisError]=useState('')
  const analysisRequest=useRef(0)
  const [strategy,setStrategy]=useState<NegotiationStrategyId>('price')
  const [reviewStatus,setReviewStatus]=useState<ReviewStatus>('Pending Review')
  const [history,setHistory]=useState<Awaited<ReturnType<typeof getNegotiationHistory>>>([])

  useEffect(()=>{let active=true;void getNegotiationHistory().then(records=>{if(active)setHistory(records)});return()=>{active=false}},[])

  useEffect(()=>{analysisRequest.current+=1;setInputs(makeInputs(order));setAnalysis(null);setAnalysisError('');setAnalysisLoading(false);setReviewStatus('Pending Review')},[order.id])
  const updateInputs:Dispatch<SetStateAction<NegotiationInputs>>=action=>{analysisRequest.current+=1;setInputs(action);setAnalysis(null);setAnalysisError('');setAnalysisLoading(false);setReviewStatus('Pending Review')}
  const contextInputs={...inputs,purchaseOrderId:order.id}
  const average=useMemo(()=>order.priceHistory.reduce((sum,item)=>sum+item.unitPrice,0)/Math.max(order.priceHistory.length,1),[order])
  const strategies=useMemo<NegotiationStrategy[]>(()=>{
    const priceReduction=Math.max(0,inputs.offeredUnitPrice-inputs.targetUnitPrice)
    const priceSaving=priceReduction*inputs.requestedQuantity
    const alternativeQuantity=Math.ceil(inputs.requestedQuantity*1.15)
    const volumePrice=inputs.offeredUnitPrice*.96
    const volumeSavings=Math.max(0,(inputs.offeredUnitPrice-volumePrice)*alternativeQuantity)
    const offeredDate=new Date(`${inputs.proposedDeliveryDate}T12:00:00`)
    const targetDate=new Date(`${inputs.preferredDeliveryDate}T12:00:00`)
    const dayDifference=Math.round((offeredDate.getTime()-targetDate.getTime())/86400000)
    const volumeLeverage=inputs.requestedQuantity>=order.minimumOrderQuantity*1.5
    return [
      {id:'price',title:'Price optimization',objective:'Reduce the unit purchasing price',target:`${formatMoney(inputs.targetUnitPrice)} / ${unitLabel(order.unit)} · ${inputs.offeredUnitPrice>0?(priceReduction/inputs.offeredUnitPrice*100).toFixed(1):'0.0'}% ${inputs.targetUnitPrice<=inputs.offeredUnitPrice?'below':'above'} offer`,impact:priceSaving,impactLabel:'estimated savings at requested quantity',rationale:inputs.offeredUnitPrice>average?`The offer is above the ${formatMoney(average)} recorded purchase average.`:inputs.offeredUnitPrice<average?`The offer is already below the ${formatMoney(average)} recorded purchase average; use the target carefully.`:'The offer aligns with the recorded purchase average.',advantages:['Clear, measurable price anchor','Grounded in purchase history'],tradeoff:'Supplier may request a longer lead time or reduced service scope.'},
      {id:'delivery',title:'Delivery optimization',objective:'Improve delivery timing and certainty',target:`Request ${inputs.preferredDeliveryDate||'a preferred date'} · ${dayDifference>0?`${dayDifference} days earlier`:dayDifference<0?`${Math.abs(dayDifference)} days after offer`:'same day as offer'}`,impact:0,impactLabel:'no price savings estimated',rationale:`Supplier has a ${supplier.onTimeRate}% historical on-time rate and ${supplier.averageDeliveryDays}-day average lead time.`,advantages:['Improves schedule predictability','Keeps price discussion separate'],tradeoff:'An earlier commitment may require flexible order scheduling or expedited freight.'},
      {id:'volume',title:'Volume negotiation',objective:'Use order quantity as negotiation leverage',target:`${alternativeQuantity.toLocaleString()} ${order.unit} · illustrative ${formatMoney(volumePrice)} unit opportunity`,impact:volumeSavings,impactLabel:'illustrative volume price estimate',rationale:volumeLeverage?`Current quantity is ${inputs.requestedQuantity.toLocaleString()}, above the ${order.minimumOrderQuantity.toLocaleString()} minimum; a larger commitment can support a volume discussion.`:`A ${alternativeQuantity.toLocaleString()}-unit scenario is shown as a discussion option. Supplier volume pricing is not known.`,advantages:['Adds a quantity-based discussion point','Can align the order with replenishment needs'],tradeoff:'Larger quantities increase working capital and inventory exposure.'},
    ]
  },[inputs,order,supplier,average])
  const selectedStrategy=strategies.find(item=>item.id===strategy)??strategies[0]
  const validate=()=>{
    if(!Number.isFinite(inputs.offeredUnitPrice)||inputs.offeredUnitPrice<=0)return 'Enter a supplier offer greater than zero.'
    if(!Number.isFinite(inputs.targetUnitPrice)||inputs.targetUnitPrice<=0)return 'Enter a target unit price greater than zero.'
    if(!Number.isInteger(inputs.requestedQuantity)||inputs.requestedQuantity<order.minimumOrderQuantity)return `Quantity must be a whole number of at least ${order.minimumOrderQuantity.toLocaleString()} ${order.unit}.`
    if(!inputs.proposedDeliveryDate||!inputs.preferredDeliveryDate)return 'Choose both proposed and preferred delivery dates.'
    return ''
  }
  const runAnalysis=async()=>{
    const validation=validate();if(validation){setAnalysisError(validation);setAnalysis(null);return}
    setAnalysisError('');setAnalysis(null);setAnalysisLoading(true)
    const requestId=++analysisRequest.current
    try{const result=await analyzeNegotiation(contextInputs,order,supplier);if(analysisRequest.current===requestId)setAnalysis(result)}catch{if(analysisRequest.current===requestId)setAnalysisError('The local demonstration analysis could not be completed. Please try again.')}finally{if(analysisRequest.current===requestId)setAnalysisLoading(false)}
  }
  const generateDraft=(tone:CommunicationTone,language:CommunicationLanguage)=>generateNegotiationDraft(contextInputs,order,supplier,strategy,tone,language)
  const confirmReview=(action:ApprovalAction)=>{
    const next:ReviewStatus=action==='Approve Strategy'?'Approved':action==='Request Revision'?'Revision Requested':'Rejected'
    setReviewStatus(next)
    const createdDate=new Date().toISOString().slice(0,10)
    const newRecord={id:`NEG-LOCAL-${String(history.length+1).padStart(3,'0')}`,supplier:supplier.name,purchaseOrder:order.id,strategy:selectedStrategy.title,targetPrice:inputs.targetUnitPrice,status:next,createdDate}
    setHistory(current=>[newRecord,...current])
  }
  const startNewAnalysis=()=>{const initial=negotiationPurchaseOrders[0];setSupplier(negotiationSuppliers[0]);setOrder(initial);setInputs(makeInputs(initial));setAnalysis(null);setAnalysisError('');setAnalysisLoading(false);setStrategy('price');setReviewStatus('Pending Review');document.getElementById('procurement-context')?.scrollIntoView({behavior:'smooth',block:'start'})}
  const scrollToHistory=()=>document.getElementById('negotiation-history')?.scrollIntoView({behavior:'smooth',block:'start'})

  return <main className="negotiation-page"><header className="neg-page-header"><div className="neg-page-title"><div className="neg-breadcrumb"><Link to="/dashboard">Dashboard</Link><ArrowRight size={13}/><span>Negotiation Copilot</span></div><div className="neg-title-line"><span className="neg-title-icon"><Handshake size={21}/></span><div><h1>AI Negotiation Copilot</h1><p>Develop smarter supplier negotiation strategies using purchasing history, contract intelligence, and AI-powered recommendations.</p></div></div></div><div className="neg-page-actions"><button className="neg-button neg-button-quiet" onClick={scrollToHistory}><History size={14}/> Negotiation history</button><button className="neg-button neg-button-primary" onClick={startNewAnalysis}><FilePlus2 size={14}/> New analysis</button></div></header>
    <div className="neg-demo-banner"><span className="demo-info">i</span><span>Frontend demonstration</span><span className="banner-separator">·</span><span>Supplier records, price history, recommendations, and review actions are local mock data.</span></div>
    <ProcurementContext supplier={supplier} order={order} inputs={inputs} setSupplier={setSupplier} setOrder={setOrder} setInputs={updateInputs}/>
    <HistoricalAnalysis order={order} supplier={supplier} offer={inputs.offeredUnitPrice} target={inputs.targetUnitPrice}/>
    <AIRecommendationPanel analysis={analysis} loading={analysisLoading} error={analysisError} onAnalyze={runAnalysis} inputs={contextInputs} order={order} supplier={supplier}/>
    <NegotiationStrategies strategies={strategies} selected={strategy} onSelect={value=>{setStrategy(value);setReviewStatus('Pending Review')}}/>
    <NegotiationComposer supplier={supplier} order={order} inputs={contextInputs} strategy={strategy} onStrategyChange={value=>{setStrategy(value);setReviewStatus('Pending Review')}} onGenerate={generateDraft}/>
    <ApprovalPanel status={reviewStatus} strategy={strategy} terms={selectedStrategy.target} savings={selectedStrategy.impact} disabled={!analysis||analysisLoading} onConfirm={confirmReview}/>
    <NegotiationHistory records={history}/>
    <div className="neg-page-footer"><Sparkles size={14}/> Simulated intelligence for product demonstration · Human review required for all procurement decisions.</div>
  </main>
}
