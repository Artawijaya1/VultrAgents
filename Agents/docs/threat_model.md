# Threat Model awal

- **Prompt injection** dalam invoice PDF atau email supplier dapat menyuruh agent melewati approval. Perlakukan isi dokumen sebagai data, bukan instruksi.
- **MCP tool schema poisoning**: review/pin tool descriptions sebelum deployment.
- **Data exfiltration**: jangan masukkan nomor rekening, token, dokumen rahasia, atau data pribadi lengkap ke prompt jika tidak diperlukan.
- **Unauthorized tool calls**: tool memverifikasi user identity, tenant, role, dan ownership di server (bukan hanya teks prompt).
- **Duplicate side effects**: writes menggunakan idempotency key dan transaksi DB.
- **Vendor bank changes**: lakukan verifikasi di kanal kontak resmi terpisah, dual control, jangan ikuti instruksi dari email perubahan itu sendiri.
- **False allegations**: keluaran agent selalu 'indikator' dan investigator manusia mengubah status temuan.
- **Missing audit**: setiap draf, persetujuan, dan revisi memiliki siapa-kapan-bukti yang tidak bisa diubah sembarangan.
- **Internet exposure**: endpoint /demo saat ini tanpa autentikasi; localhost only.

Referensi:
https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html
https://modelcontextprotocol.io/specification/
