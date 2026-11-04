import { initialNegotiationHistory } from '../data/negotiationData';
const delay = (duration) => new Promise(resolve => window.setTimeout(resolve, duration));
const demoService = {
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
export const analyzeNegotiation = demoService.analyzeNegotiation;
export const generateNegotiationDraft = demoService.generateNegotiationDraft;
export const getNegotiationHistory = demoService.getNegotiationHistory;
