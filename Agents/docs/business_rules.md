# Aturan bisnis awal

**Negotiation Copilot**
- Data wajib: PO, supplier, produk, kuantitas, harga saat ini, harga historis, harga maksimum kontrak, target, lead time, batas kewenangan.
- Output: strategi dan kontra-penawaran, alasan, nilai penghematan *jika disetujui*, draf email dan status DRAFT_ONLY.
- Dilarang mengirim email, membuat kontrak, mengganti PO, atau berkomitmen ke supplier tanpa approval eksplisit.
- Negosiasi hanya membandingkan harga barang dalam mata uang sama. Kurs, pajak, ongkir, diskon bertingkat, dan perbandingan kualitas membutuhkan fungsi tersendiri.

**Fraud Detection Agent**
- DUPLICATE_INVOICE_NUMBER: invoice number supplier sama berulang.
- PRICE_SPIKE: unit price > median historis + 25% (contoh threshold yang harus dikonfigurasi).
- BANK_CHANGE_REVIEW: fingerprint rekening pembayaran berbeda dari rekening yang telah terverifikasi.
- POSSIBLE_SPLIT_PURCHASE: beberapa invoice satu supplier < Rp5 juta dalam jendela 7 hari, total >= Rp5 juta. Ini indikator kasar, bukan bukti penghindaran approval; versi produksi harus menilai identitas requisition, pemilik, kategori, kontrak, dan periode.
- Semua temuan memerlukan review; beri kemampuan menandai *false positive* dengan alasan.
- Tidak boleh menyimpulkan korupsi, pencurian, atau pelaku bersalah secara otomatis.

**Pemisahan tugas**
- Buyer boleh membuat draf, tidak boleh menyetujui milik sendiri.
- Approver mengambil keputusan setelah autentikasi kuat dan bukti.
- Auditor baca data bukti dan jejak audit, tidak mengubah PO.
- Finance mengkaji invoice, bukan mengubah fraud scoring seenaknya.
