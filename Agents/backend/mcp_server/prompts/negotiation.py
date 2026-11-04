def negotiation_prompt(po_number: str) -> str:
    return (f"Buat strategi negosiasi untuk {po_number} berdasarkan tool yang tersedia. "
            "Berikan bukti data, opsi konsesi, batas kontrak, dan draf email. "
            "Jangan kirim email atau menyetujui transaksi. Semua usulan adalah draf.")
