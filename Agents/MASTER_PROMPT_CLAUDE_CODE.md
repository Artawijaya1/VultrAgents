# Prompt untuk Claude Code — Tahap Implementasi Agent

Saya bekerja pada repository `Artawijaya1/VultrAgents` branch `main` dengan tiga area tim:
- `Agents/` milik saya (AI Agent + MCP)
- `Backend/` milik teman database
- `Frontend/` milik teman UI

JANGAN ubah, pindah, atau hapus file apa pun di `Backend/` dan `Frontend/`.
JANGAN overwrite file existing. Sebelum mengubah kode, inspeksi dan laporkan hasil `git status`, struktur `Agents/`, serta seluruh dependensi.

Target: membangun dua AI Agent:
1. Negotiation Copilot: baca PO, histori harga, batas anggaran, susun opsi negosiasi dan draf, selalu butuh persetujuan manusia; dilarang mengirim pesan otomatis.
2. Fraud Detection Agent: flag duplikasi invoice, anomali harga, perubahan rekening menjelang invoice; wajib sertakan record ID sebagai bukti, dilarang membuat vonis fraud atau memblokir transaksi otomatis.

Arsitektur wajib: Python 3.11+, MCP Python SDK v2 (`from mcp.server import MCPServer`), mock provider yang dapat diganti adapter MySQL/API tanpa perubahan engine, MCP tools typed and read-only, agent orchestrator dengan LLM tool calling, batas jumlah tool calls, output JSON, FastAPI endpoint, unit tests. Ikuti dokumentasi SDK resmi; jangan campur `FastMCP` v1 dengan `MCPServer` v2.

Boleh memanfaatkan starter package yang sudah disediakan di `Agents/agent_core`, tetapi audit lebih dahulu sebelum melakukan perubahan.

Tahapan pengerjaan:
1. Audit repo dan buat branch kerja `feature/agents-mcp` jika belum ada.
2. Tulis kontrak data provider dan contoh mock data, lakukan unit test.
3. Bangun MCP Server + tools negotiation/fraud, uji lewat MCP Inspector.
4. Implementasikan LLM agent yang memanggil MCP client, pembatasan tool, dan trace.
5. Tambah endpoint FastAPI dan dokumentasi untuk anggota tim lainnya.
6. Jalankan test, laporkan PASS/FAIL, jangan klaim sesuatu diuji bila belum diuji.

Pada akhir setiap balasan tulis roadmap: selesai, sedang, berikutnya, kendala. Jangan push ke main tanpa permintaan eksplisit.
