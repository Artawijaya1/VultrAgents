import { initialNegotiationHistory } from '../data/negotiationData';
import { recordAuditEvent } from './auditLogService';
import {
  ApiError,
  createNegotiation,
  createNegotiationDraft as apiCreateDraft,
  createNegotiationOptions as apiCreateOptions,
  getNegotiationContext,
  getNegotiationDrafts,
  getNegotiations,
  getPriceHistory,
} from './api';

const delay = (duration) => new Promise(resolve => window.setTimeout(resolve, duration));

// ── Mock adapter (current behavior, unchanged) ──────────────────────
const mockAdapter = {
  async getNegotiationHistory() {
    await delay(120);
    return initialNegotiationHistory.map(record => ({ ...record }));
  },

  async analyzeNegotiation(input, order, supplier) {
    await delay(850);
    const historicalAverage = order.priceHistory.reduce((sum, point) => sum + point.unitPrice, 0) / order.priceHistory.length;
    const offerDifference = input.offeredUnitPrice - historicalAverage;
    const offerDifferencePercent = historicalAverage ? offerDifference / historicalAverage * 100 : 0;
    const potentialSavings = Math.max(0, input.offeredUnitPrice - input.targetUnitPrice) * input.requestedQuantity;
    const reasons = [];
    if (offerDifference > 0)
      reasons.push(`The current offer is ${Math.abs(offerDifferencePercent).toFixed(1)}% above the average of ${order.priceHistory.length} recorded purchases.`);
    else if (offerDifference < 0)
      reasons.push(`The current offer is ${Math.abs(offerDifferencePercent).toFixed(1)}% below the average of ${order.priceHistory.length} recorded purchases.`);
    else
      reasons.push('The current offer is aligned with the average of recorded purchases.');
    if (supplier.onTimeRate >= 90)
      reasons.push(`The supplier has a ${supplier.onTimeRate}% on-time delivery rate, supporting a collaborative request for improved delivery terms.`);
    else
      reasons.push(`The supplier has a ${supplier.onTimeRate}% on-time delivery rate; confirm delivery commitments before trading price concessions.`);
    if (input.requestedQuantity >= order.minimumOrderQuantity * 1.5)
      reasons.push(`The requested ${input.requestedQuantity.toLocaleString()} ${order.unit} exceed the ${order.minimumOrderQuantity.toLocaleString()} ${order.unit} minimum by at least 50%, providing a volume discussion point.`);
    if (input.offeredUnitPrice <= order.contractUnitPrice)
      reasons.push('The offer is at or below the contracted unit price.');
    else
      reasons.push('The offer is above the contracted unit price; reference the current agreement in the discussion.');
    return {
      historicalAverage,
      offerDifference,
      offerDifferencePercent,
      potentialSavings,
      recommendation: input.targetUnitPrice < input.offeredUnitPrice ? `Discuss a target of ${input.targetUnitPrice.toLocaleString(undefined, { style: 'currency', currency: 'USD' })} per ${order.unit.replace(/s$/, '')}.` : 'The target is at or above the supplier offer; validate scope and delivery terms before negotiating further.',
      approach: offerDifference > 0 ? 'Lead with historical benchmarks, then explore delivery and volume as trade-offs.' : 'Acknowledge the competitive price and focus the discussion on delivery certainty and contract terms.',
      confidence: 76 + (supplier.onTimeRate % 9),
      reasons,
    };
  },

  async generateNegotiationDraft(input, order, supplier, strategy, tone, language) {
    await delay(350);
    const indonesian = language === 'Bahasa Indonesia';
    const preferredDate = input.preferredDeliveryDate ? new Intl.DateTimeFormat(indonesian ? 'id-ID' : 'en-US', { dateStyle: 'long' }).format(new Date(`${input.preferredDeliveryDate}T12:00:00`)) : (indonesian ? 'tanggal yang disepakati bersama' : 'a mutually agreed date');
    const currency = new Intl.NumberFormat(indonesian ? 'id-ID' : 'en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(input.targetUnitPrice);
    const volumeQuantity = Math.ceil(input.requestedQuantity * 1.15).toLocaleString(indonesian ? 'id-ID' : 'en-US');
    const strategyTarget = strategy === 'price'
      ? indonesian ? `harga satuan sebesar ${currency}` : `a unit price of ${currency}`
      : strategy === 'delivery'
        ? indonesian ? `pengiriman paling lambat ${preferredDate}` : `delivery by ${preferredDate}`
        : indonesian ? `jumlah ${volumeQuantity} ${order.unit} dengan penyesuaian harga satuan` : `a quantity of ${volumeQuantity} ${order.unit} with a revised unit price`;
    const objective = indonesian
      ? strategy === 'price' ? 'optimalisasi harga' : strategy === 'delivery' ? 'optimalisasi jadwal pengiriman' : 'ketentuan volume pemesanan'
      : strategy === 'price' ? 'price optimization' : strategy === 'delivery' ? 'delivery optimization' : 'volume terms';
    if (indonesian) {
      const greeting = tone === 'Firm' ? 'Yth. Tim' : 'Halo Tim';
      const closing = tone === 'Collaborative' ? 'Kami menghargai kemitraan ini dan menantikan solusi yang baik bagi kedua pihak.' : tone === 'Firm' ? 'Mohon sampaikan persyaratan terbaik yang dapat ditawarkan minggu ini.' : 'Terima kasih atas pertimbangannya. Kami menantikan tanggapan Anda.';
      return `${greeting} ${supplier.name},\n\nKami sedang meninjau ${order.productName} untuk pesanan pembelian ${order.id}. Kami ingin mendiskusikan ${objective}, khususnya ${strategyTarget}.\n\nBerdasarkan riwayat pembelian dan kebutuhan pengadaan kami, kami berharap dapat menemukan persyaratan yang sesuai bagi kedua pihak.${input.notes.trim() ? `\n\nCatatan tambahan: ${input.notes.trim()}` : ''}\n\n${closing}\n\nHormat kami,\nTim Pengadaan PROCUREMIND`;
    }
    const opening = tone === 'Collaborative' ? `Hello ${supplier.name} team,` : `Dear ${supplier.name} team,`;
    const closing = tone === 'Firm' ? 'Please let us know your best available terms by the end of this week.' : tone === 'Collaborative' ? 'We value our partnership and look forward to finding terms that work well for both teams.' : 'We appreciate your consideration and look forward to your response.';
    return `${opening}\n\nWe are reviewing ${order.productName} for purchase order ${order.id} and would like to discuss ${objective}, specifically ${strategyTarget}.\n\nBased on our purchasing history and current requirements, we believe there may be an opportunity to align on terms that support a successful order.${input.notes.trim() ? `\n\nAdditional context: ${input.notes.trim()}` : ''}\n\n${closing}\n\nBest regards,\nProcurement Team`;
  },
};

// ── Live adapter (Backend endpoints, currently return 501) ───────────
const liveAdapter = {
  async getNegotiationHistory() {
    const raw = await getNegotiations();
    const list = Array.isArray(raw) ? raw : (raw.items ?? []);
    return list.map(item => ({
      id: item.id ?? item.negotiation_id,
      supplier: item.supplier_name ?? item.supplier ?? '—',
      purchaseOrder: item.purchase_order_id ?? item.purchaseOrder ?? '—',
      strategy: item.strategy ?? 'Price optimization',
      targetPrice: item.target_price ?? item.targetPrice ?? 0,
      status: item.status ?? 'Pending Review',
      createdDate: (item.created_at ?? item.createdDate ?? new Date().toISOString()).slice(0, 10),
    }));
  },

  async analyzeNegotiation(input, order, supplier) {
    // Calls POST /negotiations/{id}/options or POST /negotiations
    const res = await createNegotiationOptions(order.id, {
      offered_price: input.offeredUnitPrice,
      target_price: input.targetUnitPrice,
      requested_quantity: input.requestedQuantity,
      proposed_delivery_date: input.proposedDeliveryDate,
      preferred_delivery_date: input.preferredDeliveryDate,
      supplier_id: supplier.id,
    });
    return {
      historicalAverage: res.historical_average ?? 0,
      offerDifference: res.offer_difference ?? 0,
      offerDifferencePercent: res.offer_difference_percent ?? 0,
      potentialSavings: res.potential_savings ?? 0,
      recommendation: res.recommendation ?? '',
      approach: res.approach ?? '',
      confidence: res.confidence ?? 0,
      reasons: res.reasons ?? [],
    };
  },

  async generateNegotiationDraft(input, order, supplier, strategy, tone, language) {
    const res = await apiCreateDraft(order.id, {
      strategy,
      tone,
      language,
      offered_price: input.offeredUnitPrice,
      target_price: input.targetUnitPrice,
      requested_quantity: input.requestedQuantity,
      supplier_id: supplier.id,
      notes: input.notes,
    });
    return res.draft_text ?? res.draft ?? (typeof res === 'string' ? res : '');
  },
};

// ── Mode selection ──────────────────────────────────────────────────
const negotiationMode = import.meta.env.VITE_NEGOTIATION_MODE || 'mock';
export const isNegotiationMockMode = () => negotiationMode === 'mock';

function getAdapter(forceMock = false) {
  if (forceMock || negotiationMode === 'mock') return mockAdapter;
  return liveAdapter;
}

// ── Exported API ────────────────────────────────────────────────────
export async function getNegotiationHistory(forceMock = false) {
  return getAdapter(forceMock).getNegotiationHistory();
}

export async function analyzeNegotiation(input, order, supplier, forceMock = false) {
  const result = await getAdapter(forceMock).analyzeNegotiation(input, order, supplier);
  recordAuditEvent({ category: 'Negotiation', action: 'Negotiation analysis generated', entityType: 'Purchase order', entityId: order.id, outcome: 'Draft created', summary: `Negotiation guidance generated for ${order.id}.`, details: { supplierId: supplier.id, strategy: 'Analysis' } });
  return result;
}

export async function generateNegotiationDraft(input, order, supplier, strategy, tone, language, forceMock = false) {
  const draft = await getAdapter(forceMock).generateNegotiationDraft(input, order, supplier, strategy, tone, language);
  recordAuditEvent({ category: 'Negotiation', action: 'Negotiation message draft generated', entityType: 'Purchase order', entityId: order.id, outcome: 'Draft created', summary: `A ${strategy} negotiation draft was generated for ${supplier.name}.`, details: { supplierId: supplier.id, strategy, tone, language } });
  return draft;
}

export { ApiError };
