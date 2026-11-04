export type Supplier = {
  id: string
  name: string
  rating: number
  category: string
  averageDeliveryDays: number
  onTimeRate: number
  previousOrders: number
}

export type PricePoint = { date: string; unitPrice: number }
export type DeliveryRecord = {
  purchaseOrder: string
  orderedDate: string
  deliveredDate: string
  status: 'On time' | 'Delayed'
  delayDays: number
}

export type PurchaseOrder = {
  id: string
  supplierId: string
  productName: string
  category: string
  quantity: number
  unit: string
  historicalPrice: number
  currentOffer: number
  previousPurchaseDate: string
  contractId: string
  contractValidThrough: string
  contractUnitPrice: number
  paymentTerms: string
  deliveryTerms: string
  minimumOrderQuantity: number
  preferredDeliveryDate: string
  offeredDeliveryDate: string
  targetPrice: number
  priceHistory: PricePoint[]
  deliveryHistory: DeliveryRecord[]
}

export type NegotiationInputs = {
  purchaseOrderId: string
  offeredUnitPrice: number
  requestedQuantity: number
  proposedDeliveryDate: string
  targetUnitPrice: number
  preferredDeliveryDate: string
  notes: string
}

export type NegotiationStrategyId = 'price' | 'delivery' | 'volume'
export type ReviewStatus = 'Pending Review' | 'Approved' | 'Revision Requested' | 'Rejected'
export type CommunicationTone = 'Professional' | 'Collaborative' | 'Firm'
export type CommunicationLanguage = 'English' | 'Bahasa Indonesia'

export type NegotiationAnalysis = {
  historicalAverage: number
  offerDifference: number
  offerDifferencePercent: number
  potentialSavings: number
  recommendation: string
  approach: string
  confidence: number
  reasons: string[]
}

export type NegotiationHistoryRecord = {
  id: string
  supplier: string
  purchaseOrder: string
  strategy: string
  targetPrice: number
  status: ReviewStatus
  createdDate: string
}

export type ApprovalAction = 'Approve Strategy' | 'Request Revision' | 'Reject Recommendation'
