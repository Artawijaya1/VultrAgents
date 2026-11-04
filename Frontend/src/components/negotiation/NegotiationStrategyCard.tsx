import { Check, Clock3, Package, TrendingDown } from 'lucide-react'
import { NegotiationStrategyId } from '../../types/negotiation'
import { formatDate, formatMoney } from './NegotiationContext'

export type NegotiationStrategy = {
  id:NegotiationStrategyId
  title:string
  objective:string
  target:string
  impact:number
  impactLabel:string
  rationale:string
  advantages:string[]
  tradeoff:string
}

const icons={price:TrendingDown,delivery:Clock3,volume:Package}

export default function NegotiationStrategyCard({strategy,selected,onSelect}:{strategy:NegotiationStrategy;selected:boolean;onSelect:()=>void}) {
  const Icon=icons[strategy.id]
  return <button type="button" className={`neg-strategy-card ${selected?'selected':''}`} onClick={onSelect} aria-pressed={selected}><div className="strategy-top"><span className="strategy-icon"><Icon size={17}/></span>{selected&&<span className="strategy-selected"><Check size={12}/> SELECTED</span>}</div><span className="strategy-label">{strategy.id==='price'?'STRATEGY A':strategy.id==='delivery'?'STRATEGY B':'STRATEGY C'}</span><h4>{strategy.title}</h4><p className="strategy-objective">{strategy.objective}</p><div className="strategy-target"><small>PROPOSED TERMS</small><b>{strategy.target}</b></div>{strategy.impact>0&&<div className="strategy-impact"><span>{formatMoney(strategy.impact)}</span><small>{strategy.impactLabel}</small></div>}<div className="strategy-why"><b>Why consider this</b><p>{strategy.rationale}</p></div><div className="strategy-pros">{strategy.advantages.map(item=><span key={item}><Check size={12}/>{item}</span>)}</div><div className="strategy-tradeoff"><b>Potential trade-off</b><p>{strategy.tradeoff}</p></div></button>
}

export function NegotiationStrategies({strategies,selected,onSelect}:{strategies:NegotiationStrategy[];selected:NegotiationStrategyId;onSelect:(id:NegotiationStrategyId)=>void}) {return <section className="neg-section strategy-section" id="strategies"><div className="neg-section-heading"><div><span className="neg-step-label">04 / NEGOTIATION OPTIONS</span><h2>Choose a negotiation strategy</h2><p>Compare simulated outcomes and select the approach you want to prepare for review.</p></div><span className="section-icon"><Check size={18}/></span></div><div className="strategy-grid">{strategies.map(strategy=><NegotiationStrategyCard key={strategy.id} strategy={strategy} selected={selected===strategy.id} onSelect={()=>onSelect(strategy.id)}/>)}</div><p className="strategy-disclaimer">Estimated impacts are illustrative calculations from the entered terms; supplier acceptance is not predicted.</p></section>}

export function makeStrategyTargetDate(date:string){return formatDate(date)}
