import { Boxes } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function Logo() {
  return <Link className="brand" to="/" aria-label="ProcureMind AI home"><span className="brand-mark"><Boxes size={19} strokeWidth={1.7} /></span><span className="brand-name">PROCUREMIND<span> AI</span></span></Link>
}
