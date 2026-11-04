# Arsitektur

Procurement Officer -> (frontend React, belum ada) -> FastAPI -> Agent Orchestrator ->
- Negotiation Copilot -> MCP Client -> MCP Server tools -> Repository / database
- Fraud Detection Agent -> MCP Client -> MCP Server tools -> Repository / database

Demo sekarang menggunakan engine Python berbasis aturan yang sama untuk API/MCP; agent LLM dan MCP client internal belum dikonfigurasi. Jangan keliru menganggap pemanggilan fungsi Python sebagai pemanggilan protokol MCP; hal itu baru terjadi melalui host/Inspector.

Boundary: MCP tools menyediakan data/operasi terkontrol; agent memilih tools dan menjelaskan output; service menentukan perhitungan yang bisa diuji; database menegakkan integritas; approval service manusia mengotorisasi perubahan. Audit tetap wajib untuk seluruh aksi sensitif.
