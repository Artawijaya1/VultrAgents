# ProcureGuard Stage 7 — Pekerjaan terbuka setelah batch perbaikan

DOKUMEN INI ADALAH DAFTAR RISIKO DAN DEPENDENSI, BUKAN DAFTAR YANG SUDAH FIX.

| Prioritas | Temuan | Owner / syarat penutupan |
|---|---|---|
| P0 | Akses PO/sesi per pengguna belum ditegakkan oleh Agent service Bearer | Backend: login, RBAC, hak akses PO/session di proxy; tes negatif cross-user |
| P0 | Gemini direct probe menerima HTTP 400 dalam satu audit | Diagnostik body error provider dan uji ulang live setelah pembaruan probe; jangan berasumsi root cause |
| P1 | Backend asli belum diuji | Tim Backend + Agent: test mode http dengan data staging |
| P1 | Memori `InMemorySaver` tidak persisten | Pakai persistent checkpoint, session binding, TTL hanya bila deployment memerlukannya |
| P1 | Secret scan hanya mendeteksi pola standar | Audit histori Git, file lain, dan rotasi Google key lama secara manual |
| P2 | Contoh LAPTOP-01 Rp150.000 tidak realistis | Beri label DATA SIMULASI; buat contoh realistis setelah validasi test fixtures |

Pengujian lokal sebelumnya telah menghasilkan 41 unit test PASS dan memori
2 putaran yang mengingat 2 preferensi user. Hasil ini tidak membuktikan
keamanan pengguna, integrasi data asli, atau keandalan model di produksi.

Tindakan batch ini sengaja TIDAK mengubah `agent_core/` atau test fixture.
Hindari auto-fix pada security/auth dan provider schema tanpa kontrak tim.
